#!/Users/zire/.venvs/tsb/bin/python
"""
Archive an issue's media to Crestfall, the designated copy of every PDF, MP3,
and MP4. The site no longer deploys audio and the YouTube depot lives on one
machine's Desktop, so this is the copy that counts.

Each issue gets its own folder on the NAS:
    familyarchive/newsletters/sundayblender/YYYY-MM-DD/
        The-Sunday-Blender-YYYY-MM-DD-<title>.pdf   from static/pdf/ (latest version)
        YYYY-MM-DD-podcast.mp3                      from the issue folder
        [NN-]YYYY-MM-DD-<slug>.mp4                  from ~/Desktop/tsb-youtube

Usage:
    tsb-archive-media             # from inside the issue folder; needs all three files
    tsb-archive-media --all       # every issue, whatever media each one has (backfill)
    tsb-archive-media --dry-run   # list what would be copied, copy nothing
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTENT_DIR = REPO_ROOT / "content" / "posts"
PDF_DIR = REPO_ROOT / "static" / "pdf"
VIDEO_DIR = Path.home() / "Desktop" / "tsb-youtube"

NAS_HOST = "crestfall"
NAS_ROOT = "/volume1/familyarchive/newsletters/sundayblender"
SSH_OPTS = ["-o", "BatchMode=yes", "-o", "ConnectTimeout=10"]


def issue_date(issue_dir):
    """Return the issue's YYYY-MM-DD from index.md frontmatter, or None."""
    index = issue_dir / "index.md"
    if not index.is_file():
        return None
    match = re.search(r'^date:\s*["\']?(\d{4}-\d{2}-\d{2})', index.read_text(), re.MULTILINE)
    return match.group(1) if match else None


def find_one(directory, pattern):
    """The single file in directory matching pattern, or None (error if several)."""
    matches = sorted(p for p in directory.glob(pattern) if p.is_file())
    if len(matches) > 1:
        names = ", ".join(p.name for p in matches)
        raise SystemExit(f"{RED}❌ More than one match for {pattern}: {names}{NC}")
    return matches[0] if matches else None


def media_for(issue_dir, date):
    """Map pdf/mp3/mp4 to the file for this issue (None when missing)."""
    return {
        "pdf": find_one(PDF_DIR, f"The-Sunday-Blender-{date}-*.pdf"),
        "mp3": find_one(issue_dir, f"{date}-podcast.mp3"),
        # archive videos carry an NN- episode prefix; weekly ones do not
        "mp4": find_one(VIDEO_DIR, f"*{date}-*.mp4"),
    }


def ssh(command):
    return subprocess.run(["ssh", *SSH_OPTS, NAS_HOST, command], capture_output=True, text=True)


def copy(date, files, dry_run):
    dest = f"{NAS_HOST}:{NAS_ROOT}/{date}/"
    if dry_run:
        for f in files:
            print(f"  would copy {f.name}")
        return True
    # -t keeps timestamps, so reruns skip files that are already there
    result = subprocess.run(
        ["rsync", "-rt", "--partial", "-e", "ssh " + " ".join(SSH_OPTS), *map(str, files), dest],
    )
    return result.returncode == 0


def main():
    ap = argparse.ArgumentParser(description="Archive issue media to Crestfall")
    ap.add_argument("--all", action="store_true", help="archive every issue (backfill)")
    ap.add_argument("--dry-run", action="store_true", help="show what would be copied")
    args = ap.parse_args()

    if args.all:
        issue_dirs = sorted(p.parent for p in CONTENT_DIR.rglob("index.md"))
    else:
        issue_dirs = [Path.cwd()]
        if not (Path.cwd() / "index.md").is_file():
            print(f"{RED}❌ Error: index.md not found - run from the issue folder, or use --all{NC}")
            return 1

    plan = []
    for issue_dir in issue_dirs:
        date = issue_date(issue_dir)
        if not date:
            if not args.all:
                print(f"{RED}❌ Error: no date found in frontmatter{NC}")
                return 1
            continue
        media = media_for(issue_dir, date)
        missing = [kind for kind, path in media.items() if path is None]
        if not args.all and missing:
            print(f"{RED}❌ Missing {', '.join(missing)} for {date}:{NC}")
            hints = {
                "pdf": "run tsb-make-pdf",
                "mp3": "run tsb-make-podcast",
                "mp4": f"run tsb-make-youtube {issue_dir}",
            }
            for kind in missing:
                print(f"   {kind}: {hints[kind]}")
            return 1
        files = [path for path in media.values() if path]
        if files:
            plan.append((date, files))

    if not plan:
        print(f"{YELLOW}Nothing to archive{NC}")
        return 0

    if not args.dry_run:
        dirs = " ".join(f"'{NAS_ROOT}/{date}'" for date, _ in plan)
        result = ssh(f"mkdir -p {dirs}")
        if result.returncode != 0:
            print(f"{RED}❌ Can't reach {NAS_HOST} (are you home, with Astrill off?){NC}")
            print(result.stderr.strip())
            return 1

    failed = []
    for date, files in plan:
        print(f"{BLUE}📦 {date}{NC} ({', '.join(f.suffix[1:] for f in files)})")
        if not copy(date, files, args.dry_run):
            failed.append(date)

    print()
    if failed:
        print(f"{RED}❌ Failed: {', '.join(failed)} - run again to retry{NC}")
        return 1
    verb = "Would archive" if args.dry_run else "Archived"
    print(f"{GREEN}✅ {verb} {len(plan)} issue(s) to {NAS_HOST}:{NAS_ROOT}/{NC}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
