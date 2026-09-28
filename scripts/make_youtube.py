#!/Users/zire/.venvs/tsb/bin/python
"""
Build the YouTube-ready MP4 for a single Sunday Blender issue.

Wraps the issue's podcast MP3 in an MP4 (blurred hero backdrop, hero picture,
issue title, date, and logo, looped at 2 fps under AAC audio) — the same
pipeline as youtube_archive.py, which is the batch tool for the historical
back-catalogue. This tool is for the weekly workflow: run it on an issue
folder after the podcast MP3 exists and upload the produced files.

For the issue folder (the one holding index.md) this writes to the video
depot (~/Desktop/tsb-youtube, kept out of git and Vercel):
    YYYY-MM-DD-<slug>.mp4            the video to upload
    YYYY-MM-DD-<slug>-thumbnail.jpg  custom thumbnail (1280x720)
    YYYY-MM-DD-<slug>.txt            title, description, tags to paste

Usage (from anywhere):
    tsb-make-youtube content/posts/2026/0927     # issue folder, absolute or relative
    tsb-make-youtube --force ...                 # re-encode if the MP4 already exists
    tsb-make-youtube --out DIR ...               # write outputs elsewhere

Requires ffmpeg/ffprobe on PATH and Pillow (both in the tsb venv).
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from youtube_archive import (  # noqa: E402
    DEFAULT_OUT, GREEN, RED, YELLOW, NC,
    build, load_episodes,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


def find_issue_dir(working_dir: Path) -> Path:
    """Resolve the issue folder: must contain index.md and belong to the repo."""
    working_dir = working_dir.resolve()
    if (working_dir / "index.md").is_file():
        return working_dir
    # convenience: accept the date (YYYY-MM-DD) and look it up in content/posts
    date = working_dir.name
    matches = [d.parent for d in REPO_ROOT.rglob("index.md")
               if d.parent.name == date or date in d.parent.name]
    if len(matches) == 1:
        return matches[0].resolve()
    raise FileNotFoundError(
        f"no index.md in {working_dir} and no unique issue folder matching {date!r}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("issue", nargs="?", default=".",
                    help="issue folder containing index.md (or its date), default: current dir")
    ap.add_argument("--out", type=Path, default=None,
                    help=f"output folder (default: {DEFAULT_OUT}, the video depot)")
    ap.add_argument("--force", action="store_true", help="re-encode if the MP4 already exists")
    args = ap.parse_args()

    for tool in ("ffmpeg", "ffprobe"):
        if subprocess_missing(tool):
            print(f"{RED}{tool} not found on PATH{NC}")
            return 1

    try:
        issue_dir = find_issue_dir(Path(args.issue))
    except FileNotFoundError as exc:
        print(f"{RED}{exc}{NC}")
        return 1

    episodes = load_episodes(None)  # full list, so episode numbering matches the archive
    episode = next((ep for ep in episodes if ep.source_dir == issue_dir), None)
    if episode is None:
        print(f"{RED}no podcast episode in {issue_dir}{NC}\n"
              f"Check that index.md has podcast.enabled: true, a podcast file, "
              f"and a featured_image that exist.")
        return 1

    out_dir = args.out.resolve() if args.out else DEFAULT_OUT
    print(f"Issue : {episode.title}")
    print(f"Date  : {episode.date:%Y-%m-%d}  (episode {episode.number:02d})")
    print(f"MP3   : {episode.mp3.name}")
    print(f"Output: {out_dir}/{episode.stem}.mp4\n")

    result = build(episode, out_dir, args.force)
    print(result)

    if result.startswith(("+", "=")):
        print(f"\n{GREEN}Done.{NC} Upload checklist:")
        print(f"  video     {out_dir / (episode.stem + '.mp4')}")
        print(f"  thumbnail {out_dir / (episode.stem + '-thumbnail.jpg')}")
        print(f"  metadata  {out_dir / (episode.stem + '.txt')}  (title, description, tags, playlist)")
        return 0
    return 1


def subprocess_missing(tool: str) -> bool:
    import subprocess
    return subprocess.run(["which", tool], capture_output=True).returncode != 0


if __name__ == "__main__":
    sys.exit(main())
