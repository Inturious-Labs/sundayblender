#!/usr/bin/env python3
"""
Build YouTube-ready videos for every archived Sunday Blender podcast episode.

YouTube does not accept audio-only uploads, so each MP3 is wrapped in an MP4:
a single 1920x1080 frame (blurred hero backdrop, the hero picture, the issue
title, the date, and the logo) looped at 2 fps under the AAC-encoded audio.
The same frame is saved as a 1280x720 JPG for use as the custom thumbnail.

For every episode the output folder receives:
    NN-YYYY-MM-DD-slug.mp4            the video to upload
    NN-YYYY-MM-DD-slug-thumbnail.jpg  custom thumbnail
    NN-YYYY-MM-DD-slug.txt            title, description, tags to paste
plus INDEX.md listing all episodes in upload order (oldest first).

Usage (from anywhere):
    scripts/youtube_archive.py                  # all episodes -> ~/Desktop/tsb-youtube
    scripts/youtube_archive.py --out DIR        # different output folder
    scripts/youtube_archive.py --only 2026-06-21
    scripts/youtube_archive.py --force          # re-encode existing videos
    scripts/youtube_archive.py --verify         # only check existing output
    scripts/youtube_archive.py --jobs 4         # parallel encodes (default 2)

Requires ffmpeg/ffprobe on PATH and Pillow for python3.
"""

import argparse
import concurrent.futures
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from process_podcast import NEWSLETTER_DESC  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = REPO_ROOT / "content" / "posts"
LOGO = REPO_ROOT / "static" / "img" / "logo.png"
DEFAULT_OUT = Path.home() / "Desktop" / "tsb-youtube"

SITE_URL = "https://weekly.sundayblender.com"
SITE_LABEL = "weekly.sundayblender.com"
SHOW_LABEL = "THE SUNDAY BLENDER PODCAST"
PLAYLIST = "The Sunday Blender Podcast"
TAGS = [
    "The Sunday Blender", "news for kids", "kids news", "podcast for kids",
    "weekly news", "current events for kids", "learn English", "news podcast",
    "children's news", "world news for kids",
]
YOUTUBE_TITLE_MAX = 100

FRAME_W, FRAME_H = 1920, 1080
FPS = 2
FONT_DIR = Path("/System/Library/Fonts/Supplemental")
FONT_BOLD = FONT_DIR / "Arial Bold.ttf"
FONT_REGULAR = FONT_DIR / "Arial.ttf"

GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
NC = "\033[0m"


@dataclass
class Episode:
    number: int
    date: datetime
    title: str
    slug: str
    description: str
    hero: Path
    mp3: Path
    shownotes: str
    source_dir: Path

    @property
    def stem(self) -> str:
        return f"{self.number:02d}-{self.date:%Y-%m-%d}-{self.slug}"

    @property
    def youtube_title(self) -> str:
        date = f"{self.date:%b} {self.date.day}, {self.date:%Y}"
        full = f"{self.title} | The Sunday Blender · {date}"
        if len(full) <= YOUTUBE_TITLE_MAX:
            return full
        return f"{self.title} · {date}"[:YOUTUBE_TITLE_MAX]

    @property
    def youtube_description(self) -> str:
        """Episode-specific lines first, then the standard blurb and the subscribe link."""
        issue_line = ""
        if self.shownotes:
            for para in self.shownotes.split("\n\n"):
                if para.startswith("In the issue of"):
                    issue_line = para.strip()
                    break
        if not issue_line:
            issue_line = f"In the issue of {self.date:%b %d}, {self.description}"
        return f"""{issue_line}

📖 Read the full newsletter article with pictures, comments, and likes:
{SITE_URL}/p/{self.slug}/

{NEWSLETTER_DESC}

📧 Subscribe to The Sunday Blender newsletter with email:
{SITE_URL}"""


# ---------------------------------------------------------------- front matter

def split_frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return ""
    parts = text.split("---", 2)
    return parts[1] if len(parts) >= 3 else ""


def field(frontmatter: str, name: str) -> str:
    match = re.search(rf'^[ \t]*{name}:\s*["\']?(.*?)["\']?\s*$', frontmatter, re.MULTILINE)
    return match.group(1).strip() if match else ""


def block_field(frontmatter: str, name: str) -> str:
    """Read an indented block scalar (`name: |`) and return it dedented."""
    match = re.search(rf'^(\s*){name}:\s*\|\s*$', frontmatter, re.MULTILINE)
    if not match:
        return ""
    key_indent = len(match.group(1))
    lines = []
    for line in frontmatter[match.end():].splitlines()[1:]:
        if line.strip() == "":
            lines.append("")
            continue
        indent = len(line) - len(line.lstrip())
        if indent <= key_indent:
            break
        lines.append(line)
    if not lines:
        return ""
    body_indent = min(len(l) - len(l.lstrip()) for l in lines if l.strip())
    return "\n".join(l[body_indent:] for l in lines).strip()


def load_episodes(only: str | None) -> list[Episode]:
    found = []
    for index in sorted(CONTENT_DIR.rglob("index.md")):
        fm = split_frontmatter(index.read_text())
        if not fm or field(fm, "draft") == "true":
            continue
        if not re.search(r"^podcast:\s*$", fm, re.MULTILINE) or field(fm, "enabled") != "true":
            continue
        mp3 = index.parent / field(fm, "file")
        if not mp3.is_file():
            print(f"{YELLOW}skip {index.parent}: podcast file missing{NC}")
            continue
        date = datetime.strptime(field(fm, "date")[:10], "%Y-%m-%d")
        hero = index.parent / field(fm, "featured_image")
        if not hero.is_file():
            print(f"{YELLOW}skip {index.parent}: hero image missing{NC}")
            continue
        found.append((date, index, fm, mp3, hero))

    found.sort(key=lambda item: item[0])
    episodes = []
    for number, (date, index, fm, mp3, hero) in enumerate(found, start=1):
        episodes.append(Episode(
            number=number,
            date=date,
            title=field(fm, "title"),
            slug=field(fm, "slug") or index.parent.name,
            description=field(fm, "description"),
            hero=hero,
            mp3=mp3,
            shownotes=block_field(fm, "shownotes"),
            source_dir=index.parent,
        ))
    if only:
        episodes = [ep for ep in episodes if f"{ep.date:%Y-%m-%d}" == only]
    return episodes


# ---------------------------------------------------------------------- frame

def load_font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(str(path), size)
    except OSError:
        return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size)


def wrap_text(draw, text, font, max_width):
    words, lines, current = text.split(), [], ""
    for word in words:
        trial = f"{current} {word}".strip()
        if draw.textlength(trial, font=font) <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def fit_title(draw, text, max_width, max_lines, start=68, floor=40):
    size = start
    while True:
        font = load_font(FONT_BOLD, size)
        lines = wrap_text(draw, text, font, max_width)
        if len(lines) <= max_lines or size <= floor:
            return font, lines
        size -= 4


def rounded(img: Image.Image, radius: int) -> Image.Image:
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, img.width - 1, img.height - 1], radius, fill=255)
    out = img.convert("RGBA")
    out.putalpha(mask)
    return out


def render_frame(ep: Episode) -> Image.Image:
    hero = Image.open(ep.hero).convert("RGB")

    # Backdrop: hero scaled to cover the frame, blurred, darkened.
    scale = max(FRAME_W / hero.width, FRAME_H / hero.height)
    bg = hero.resize((round(hero.width * scale), round(hero.height * scale)), Image.LANCZOS)
    left = (bg.width - FRAME_W) // 2
    top = (bg.height - FRAME_H) // 2
    bg = bg.crop((left, top, left + FRAME_W, top + FRAME_H)).filter(ImageFilter.GaussianBlur(40))
    bg = Image.blend(bg, Image.new("RGB", bg.size, (12, 10, 8)), 0.55).convert("RGBA")

    # Hero picture on the left, fitted into a box, with rounded corners and a shadow.
    box_w, box_h = 1040, 840
    fit = min(box_w / hero.width, box_h / hero.height)
    pic = hero.resize((round(hero.width * fit), round(hero.height * fit)), Image.LANCZOS)
    pic_x = 100 + (box_w - pic.width) // 2
    pic_y = (FRAME_H - pic.height) // 2
    shadow = Image.new("RGBA", (pic.width + 80, pic.height + 80), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle([40, 48, pic.width + 40, pic.height + 56], 28, fill=(0, 0, 0, 170))
    shadow = shadow.filter(ImageFilter.GaussianBlur(22))
    bg.alpha_composite(shadow, (pic_x - 40, pic_y - 40))
    bg.alpha_composite(rounded(pic, 24), (pic_x, pic_y))

    # Text column on the right.
    draw = ImageDraw.Draw(bg)
    col_x, col_w = 1240, 580
    label_font = load_font(FONT_BOLD, 28)
    date_font = load_font(FONT_REGULAR, 36)
    site_font = load_font(FONT_REGULAR, 30)
    title_font, title_lines = fit_title(draw, ep.title, col_w, max_lines=5)
    title_lh = int(title_font.size * 1.18)

    logo = Image.open(LOGO).convert("RGBA").resize((120, 120), Image.LANCZOS)
    logo = rounded(logo, 22)

    block_h = 120 + 36 + 28 + 24 + title_lh * len(title_lines) + 28 + 36
    y = (FRAME_H - block_h) // 2
    bg.alpha_composite(logo, (col_x, y))
    y += 120 + 36
    draw.text((col_x, y), SHOW_LABEL, font=label_font, fill=(232, 200, 150, 255))
    y += 28 + 24
    for line in title_lines:
        draw.text((col_x, y), line, font=title_font, fill=(255, 255, 255, 255))
        y += title_lh
    y += 28
    draw.text((col_x, y), f"{ep.date:%-d %B %Y}", font=date_font, fill=(215, 215, 215, 255))

    draw.text((col_x, FRAME_H - 90), SITE_LABEL, font=site_font, fill=(190, 190, 190, 255))
    return bg.convert("RGB")


# ---------------------------------------------------------------------- video

def probe_duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return float(out)


def encode(ep: Episode, frame_png: Path, out_mp4: Path) -> None:
    duration = probe_duration(ep.mp3)
    cmd = [
        "ffmpeg", "-v", "error", "-y",
        "-loop", "1", "-framerate", str(FPS), "-i", str(frame_png),
        "-i", str(ep.mp3),
        "-t", f"{duration:.3f}",
        "-c:v", "libx264", "-preset", "veryfast", "-tune", "stillimage",
        "-crf", "23", "-pix_fmt", "yuv420p", "-r", str(FPS),
        "-g", str(FPS * 30), "-keyint_min", str(FPS * 30), "-sc_threshold", "0",
        "-c:a", "aac", "-b:a", "160k", "-ar", "44100",
        "-movflags", "+faststart",
        "-metadata", f"title={ep.title}",
        "-metadata", "artist=The Sunday Blender",
        "-metadata", f"date={ep.date:%Y-%m-%d}",
        str(out_mp4),
    ]
    subprocess.run(cmd, check=True)


def write_metadata(ep: Episode, out_dir: Path) -> None:
    text = f"""YOUTUBE TITLE ({len(ep.youtube_title)}/{YOUTUBE_TITLE_MAX} chars)
{ep.youtube_title}

DESCRIPTION
{ep.youtube_description}

TAGS
{", ".join(TAGS)}

RECORDING DATE (Show more > Recording date)
{ep.date:%Y-%m-%d}

PLAYLIST
{PLAYLIST}

THUMBNAIL
{ep.stem}-thumbnail.jpg

SOURCE
{ep.source_dir.relative_to(REPO_ROOT)}/
"""
    (out_dir / f"{ep.stem}.txt").write_text(text)


def build(ep: Episode, out_dir: Path, force: bool) -> str:
    out_mp4 = out_dir / f"{ep.stem}.mp4"
    thumb = out_dir / f"{ep.stem}-thumbnail.jpg"
    write_metadata(ep, out_dir)
    if out_mp4.exists() and thumb.exists() and not force:
        return f"= {ep.stem}  (exists, skipped)"

    frame = render_frame(ep)
    frame.resize((1280, 720), Image.LANCZOS).save(thumb, "JPEG", quality=88, optimize=True)
    with tempfile.TemporaryDirectory() as tmp:
        frame_png = Path(tmp) / "frame.png"
        frame.save(frame_png, "PNG")
        # Encode to a temporary name so an interrupted run never leaves a
        # truncated .mp4 that a later run would skip as finished.
        partial = out_mp4.with_suffix(".part.mp4")
        encode(ep, frame_png, partial)
        partial.replace(out_mp4)
    size_mb = out_mp4.stat().st_size / 1_000_000
    return f"+ {ep.stem}  ({size_mb:.0f} MB)"


# --------------------------------------------------------------------- verify

def verify(episodes: list[Episode], out_dir: Path) -> bool:
    ok = True
    rows = []
    for ep in episodes:
        out_mp4 = out_dir / f"{ep.stem}.mp4"
        thumb = out_dir / f"{ep.stem}-thumbnail.jpg"
        if not out_mp4.exists() or not thumb.exists():
            rows.append((ep.stem, "MISSING", "", ""))
            ok = False
            continue
        want = probe_duration(ep.mp3)
        got = probe_duration(out_mp4)
        drift = abs(want - got)
        streams = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "stream=codec_name,width,height",
             "-of", "csv=p=0", str(out_mp4)], capture_output=True, text=True).stdout.split()
        has_video = any(line.startswith("h264,1920,1080") for line in streams)
        has_audio = any(line.startswith("aac") for line in streams)
        status = "ok" if drift < 1.0 and has_video and has_audio else "BAD"
        if status != "ok":
            ok = False
        size_mb = out_mp4.stat().st_size / 1_000_000
        rows.append((ep.stem, status, f"{got/60:.1f} min", f"{size_mb:.0f} MB"))
    width = max(len(r[0]) for r in rows)
    for stem, status, dur, size in rows:
        color = GREEN if status == "ok" else RED
        print(f"{color}{status:<8}{NC} {stem:<{width}}  {dur:>9}  {size:>7}")
    return ok


def write_index(episodes: list[Episode], out_dir: Path) -> None:
    lines = [
        "# The Sunday Blender — YouTube archive uploads",
        "",
        f"Generated {datetime.now():%Y-%m-%d %H:%M}. Upload in this order (oldest first) so the channel reads chronologically.",
        "",
        "Per episode: upload the `.mp4`, paste title + description + tags from the `.txt`, set the custom thumbnail from the `-thumbnail.jpg`, set the recording date, add to the playlist.",
        "",
        "| # | Date | Title | Length | Video | Done |",
        "|---|------|-------|--------|-------|------|",
    ]
    for ep in episodes:
        out_mp4 = out_dir / f"{ep.stem}.mp4"
        mins = probe_duration(ep.mp3) / 60
        size = f"{out_mp4.stat().st_size / 1_000_000:.0f} MB" if out_mp4.exists() else "—"
        lines.append(f"| {ep.number:02d} | {ep.date:%Y-%m-%d} | {ep.title} | {mins:.0f} min | `{ep.stem}.mp4` ({size}) | [ ] |")
    (out_dir / "INDEX.md").write_text("\n".join(lines) + "\n")


# ----------------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--only", metavar="YYYY-MM-DD", help="build a single episode by date")
    ap.add_argument("--force", action="store_true", help="re-encode videos that already exist")
    ap.add_argument("--verify", action="store_true", help="only verify existing output")
    ap.add_argument("--jobs", type=int, default=2, help="parallel encodes (default 2)")
    args = ap.parse_args()

    for tool in ("ffmpeg", "ffprobe"):
        if subprocess.run(["which", tool], capture_output=True).returncode != 0:
            print(f"{RED}{tool} not found on PATH{NC}")
            return 1

    episodes = load_episodes(args.only)
    if not episodes:
        print(f"{RED}no podcast episodes found{NC}")
        return 1
    args.out.mkdir(parents=True, exist_ok=True)

    if not args.verify:
        print(f"Building {len(episodes)} episode(s) into {args.out} with {args.jobs} parallel encodes\n")
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
            futures = {pool.submit(build, ep, args.out, args.force): ep for ep in episodes}
            for fut in concurrent.futures.as_completed(futures):
                ep = futures[fut]
                try:
                    print(fut.result())
                except Exception as exc:  # noqa: BLE001
                    print(f"{RED}! {ep.stem}: {exc}{NC}")
        if not args.only:
            write_index(episodes, args.out)
        print()

    print("Verification (duration must match the MP3, H.264 1920x1080 + AAC):")
    good = verify(episodes, args.out)
    print()
    print(f"{GREEN}all good{NC}" if good else f"{RED}problems found, see above{NC}")
    return 0 if good else 1


if __name__ == "__main__":
    sys.exit(main())
