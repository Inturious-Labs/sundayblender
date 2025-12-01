#!/usr/bin/env python3
"""
Process podcast for Sunday Blender Newsletter.
Converts m4a to mp3, updates frontmatter with metadata, and generates shownotes.

Usage: Run from within the article folder (content/posts/YYYY/MM/MMDD/)
       tsb-process-podcast
"""

import sys
import re
import subprocess
from pathlib import Path
from datetime import datetime

# Colors for terminal output
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'

BASE_URL = "https://weekly.sundayblender.com"


def find_m4a_file(cwd):
    """Find m4a file in current directory."""
    m4a_files = list(cwd.glob("*.m4a"))
    if not m4a_files:
        return None
    return m4a_files[0]


def convert_to_mp3(m4a_file, output_file):
    """Convert m4a to mp3 using ffmpeg."""
    cmd = [
        'ffmpeg', '-i', str(m4a_file),
        '-codec:a', 'libmp3lame',
        '-qscale:a', '2',
        str(output_file),
        '-y'
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


def get_audio_duration(mp3_file):
    """Get duration in seconds using ffprobe."""
    cmd = [
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        str(mp3_file)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return int(float(result.stdout.strip()))
    return 0


def get_file_size(file_path):
    """Get file size in bytes."""
    return file_path.stat().st_size


def parse_frontmatter(content):
    """Parse frontmatter from markdown content."""
    if not content.startswith('---'):
        return None, content

    parts = content.split('---', 2)
    if len(parts) < 3:
        return None, content

    return parts[1], parts[2]


def extract_field(frontmatter, field):
    """Extract a field value from frontmatter."""
    pattern = rf'^{field}:\s*["\']?(.*?)["\']?\s*$'
    match = re.search(pattern, frontmatter, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return ""


def generate_shownotes(date_str, description, slug):
    """Generate enhanced show notes."""
    newsletter_desc = "The Sunday Blender is a weekly newsletter that reports top trending news around the world. It's made for curious English-speaking kids aged 8~15 who aspire for a bigger world and nurture a life-long habit of reading. Every new issue is delivered to your email inbox on Saturday. Each issue comes with 20~25 stories. Each story has no more than 100 words, in plain English with a picture. These stories cover Technology, Global, Economy & Finance, Nature & Environment, Science, Lifestyle & Culture, Sports, History, Art, and Comedy. It's about 10~15 minutes of reading time."

    # Format date
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        formatted_date = date_obj.strftime('%b %d')
        transition = f"In the issue of {formatted_date}, "
    except:
        transition = ""

    article_url = f"{BASE_URL}/p/{slug}/" if slug else BASE_URL

    shownotes = f"""{newsletter_desc}

{transition}{description}

📖 Read the full newsletter article with pictures, comments, and likes:
{article_url}

📧 Subscribe to The Sunday Blender newsletter with email:
{BASE_URL}

🎧 Listen on:
• Apple Podcasts: https://podcasts.apple.com/us/podcast/the-sunday-blender-podcast/id1853996806
• Spotify: https://open.spotify.com/show/0p6Boxgcyy9eJzdBQlu4CG
• 小宇宙 (Xiaoyuzhou): https://www.xiaoyuzhoufm.com/podcast/691d248b88967822c085fda5"""

    return shownotes


def update_frontmatter(frontmatter, mp3_filename, duration, filesize, shownotes):
    """Update podcast section in frontmatter."""

    # Format shownotes for YAML (indent each line)
    shownotes_lines = shownotes.split('\n')
    shownotes_yaml = '\n'.join(f'    {line}' for line in shownotes_lines)

    # Build new podcast section
    new_podcast = f"""podcast:
  enabled: true
  file: "{mp3_filename}"
  duration: {duration}
  filesize: {filesize}
  shownotes: |
{shownotes_yaml}"""

    # Remove existing podcast section
    # Match from "podcast:" to the next top-level key or end
    pattern = r'^podcast:.*?(?=^[a-z]|\Z)'
    frontmatter = re.sub(pattern, '', frontmatter, flags=re.MULTILINE | re.DOTALL)

    # Add new podcast section before the closing
    frontmatter = frontmatter.rstrip() + '\n' + new_podcast + '\n'

    return frontmatter


def main():
    cwd = Path.cwd()
    index_file = cwd / "index.md"

    print(f"{BLUE}🎙️  Sunday Blender Podcast Processor{NC}")
    print(f"{BLUE}{'━' * 50}{NC}")
    print()

    # Check index.md exists
    if not index_file.exists():
        print(f"{RED}❌ Error: index.md not found{NC}")
        sys.exit(1)

    # Read and parse frontmatter
    content = index_file.read_text()
    frontmatter, body = parse_frontmatter(content)

    if not frontmatter:
        print(f"{RED}❌ Error: Could not parse frontmatter{NC}")
        sys.exit(1)

    # Extract fields
    date_str = extract_field(frontmatter, 'date')
    description = extract_field(frontmatter, 'description')
    slug = extract_field(frontmatter, 'slug')

    if not date_str:
        print(f"{RED}❌ Error: No date found in frontmatter{NC}")
        sys.exit(1)

    print(f"{GREEN}📅 Date: {date_str}{NC}")

    # Find m4a file
    m4a_file = find_m4a_file(cwd)
    if not m4a_file:
        print(f"{RED}❌ Error: No .m4a file found{NC}")
        print(f"{YELLOW}💡 Download audio from NotebookLM first{NC}")
        sys.exit(1)

    print(f"{GREEN}🎵 Found: {m4a_file.name}{NC}")

    # Output filename
    mp3_filename = f"{date_str}-podcast.mp3"
    mp3_file = cwd / mp3_filename

    # Check ffmpeg
    if subprocess.run(['which', 'ffmpeg'], capture_output=True).returncode != 0:
        print(f"{RED}❌ Error: ffmpeg not installed{NC}")
        print(f"{YELLOW}💡 Install with: brew install ffmpeg{NC}")
        sys.exit(1)

    # Convert to mp3
    print(f"{BLUE}🔄 Converting to MP3...{NC}")
    if not convert_to_mp3(m4a_file, mp3_file):
        print(f"{RED}❌ Error: Conversion failed{NC}")
        sys.exit(1)

    print(f"{GREEN}✅ Created: {mp3_filename}{NC}")

    # Get metadata
    duration = get_audio_duration(mp3_file)
    filesize = get_file_size(mp3_file)

    duration_min = duration // 60
    duration_sec = duration % 60
    filesize_mb = filesize / (1024 * 1024)

    print(f"{GREEN}⏱️  Duration: {duration}s ({duration_min}m {duration_sec}s){NC}")
    print(f"{GREEN}📦 Size: {filesize} bytes ({filesize_mb:.1f} MB){NC}")

    # Generate shownotes
    print(f"{BLUE}📝 Generating show notes...{NC}")
    shownotes = generate_shownotes(date_str, description, slug)

    # Update frontmatter
    print(f"{BLUE}📄 Updating frontmatter...{NC}")
    updated_frontmatter = update_frontmatter(frontmatter, mp3_filename, duration, filesize, shownotes)

    # Write back
    new_content = f"---{updated_frontmatter}---{body}"
    index_file.write_text(new_content)

    print()
    print(f"{GREEN}{'━' * 50}{NC}")
    print(f"{GREEN}✅ Podcast processing complete!{NC}")
    print()
    print(f"{BLUE}Updated:{NC}")
    print(f"  • podcast.enabled: true")
    print(f"  • podcast.file: {mp3_filename}")
    print(f"  • podcast.duration: {duration}")
    print(f"  • podcast.filesize: {filesize}")
    print(f"  • podcast.shownotes: (regenerated)")
    print()


if __name__ == "__main__":
    main()
