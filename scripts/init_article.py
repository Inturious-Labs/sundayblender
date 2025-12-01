#!/usr/bin/env python3
"""
Initialize a new Sunday Blender article with prepopulated index.md

Usage: Run from within the article folder (content/posts/YYYY/MM/MMDD/)
       tsb-init-article
"""

import sys
import subprocess
from datetime import datetime
from pathlib import Path

# Colors for terminal output
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
PURPLE = '\033[0;35m'
GRAY = '\033[0;90m'
NC = '\033[0m'  # No Color
BOLD = '\033[1m'

def get_repo_root_from_cwd():
    """Find the repo root by looking for content/posts in parent dirs."""
    cwd = Path.cwd()
    # Walk up to find the repo root (where content/posts exists)
    for parent in [cwd] + list(cwd.parents):
        if (parent / "content" / "posts").exists() and (parent / "hugo.toml").exists():
            return parent
    return None

def parse_date_from_path():
    """
    Parse publication date from current directory path.
    Expected format: .../content/posts/YYYY/MM/MMDD/
    Returns (year, month, day) tuple or None if invalid.
    """
    cwd = Path.cwd()
    parts = cwd.parts

    # Find "posts" in path and get the date components after it
    try:
        posts_idx = parts.index("posts")
        if len(parts) >= posts_idx + 4:
            year = parts[posts_idx + 1]
            month = parts[posts_idx + 2]
            mmdd = parts[posts_idx + 3]

            # Validate format
            if (len(year) == 4 and year.isdigit() and
                len(month) == 2 and month.isdigit() and
                len(mmdd) == 4 and mmdd.isdigit()):
                day = mmdd[2:4]
                return (year, month, day)
    except (ValueError, IndexError):
        pass

    return None

def get_published_posts(repo_root, limit=3):
    """
    Find the most recent published posts (draft: false) that are committed to git.
    Returns list of (date, title, slug) tuples.
    """
    posts_dir = repo_root / "content" / "posts"
    posts = []

    for index_file in posts_dir.rglob("index.md"):
        try:
            content = index_file.read_text()

            # Check if it's published (draft: false)
            if "draft: false" not in content:
                continue

            # Check if it's committed (not in git status)
            relative_path = index_file.relative_to(repo_root)
            result = subprocess.run(
                ["git", "status", "--porcelain", str(relative_path)],
                capture_output=True,
                text=True,
                cwd=repo_root
            )
            if result.stdout.strip():
                # File has uncommitted changes, skip
                continue

            # Extract date, title, and slug from frontmatter
            date_str = None
            title = None
            slug = None

            in_frontmatter = False
            for line in content.split('\n'):
                if line.strip() == '---':
                    if in_frontmatter:
                        break
                    in_frontmatter = True
                    continue

                if in_frontmatter:
                    if line.startswith('date:'):
                        date_str = line.replace('date:', '').strip().split('T')[0]
                    elif line.startswith('title:'):
                        title = line.replace('title:', '').strip().strip('"')
                    elif line.startswith('slug:'):
                        slug = line.replace('slug:', '').strip().strip('"')

            if date_str and title and slug:
                posts.append((date_str, title, slug))

        except Exception as e:
            continue

    # Sort by date (newest first) and return top N
    posts.sort(key=lambda x: x[0], reverse=True)
    return posts[:limit]

def format_date_readable(date_str):
    """Convert YYYY-MM-DD to 'Month DD, YYYY' format."""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%B %d, %Y")
    except:
        return date_str

def generate_previous_issues_section(repo_root):
    """Generate the Previous Issues markdown section."""
    posts = get_published_posts(repo_root, limit=3)

    if not posts:
        return ""

    lines = [
        "",
        "---",
        "",
        "## Previous Issues",
        "",
        "---",
        ""
    ]

    for date_str, title, slug in posts:
        formatted_date = format_date_readable(date_str)
        url = f"https://weekly.sundayblender.com/p/{slug}"
        lines.append(f"{formatted_date}, **[{title}]({url})**")
        lines.append("")

    return '\n'.join(lines)

def create_article():
    """Create index.md in the current directory."""
    cwd = Path.cwd()
    post_file = cwd / "index.md"

    # Check if index.md already exists
    if post_file.exists():
        print(f"{YELLOW}index.md already exists in this folder{NC}")
        confirm = input(f"{BLUE}Overwrite? [y/N]: {NC}").strip().lower()
        if confirm != 'y':
            return False

    # Parse date from folder path
    date_parts = parse_date_from_path()
    if not date_parts:
        print(f"{RED}Cannot determine date from folder path{NC}")
        print(f"{YELLOW}Expected path format: content/posts/YYYY/MM/MMDD/{NC}")
        return False

    year, month, day = date_parts
    publication_date = f"{year}-{month}-{day}"

    # Find repo root for previous issues
    repo_root = get_repo_root_from_cwd()

    # Show date info
    try:
        dt = datetime.strptime(publication_date, "%Y-%m-%d")
        day_name = dt.strftime("%A, %B %d, %Y")
        print(f"{BLUE}Publication date: {day_name}{NC}")
    except:
        pass

    # Generate placeholder values
    title = "Title Placeholder"
    slug = f"title-placeholder-{month}{day}"
    description = "Description placeholder - brief summary of this issue"

    # Generate previous issues section
    previous_issues = ""
    if repo_root:
        print(f"{BLUE}Generating previous issues links...{NC}")
        previous_issues = generate_previous_issues_section(repo_root)

    # Create index.md content
    content = f'''---
title: "{title}"
date: {publication_date}
slug: {slug}
description: "{description}"
tags: ["Tag1", "Tag2", "Tag3", "Tag4", "Tag5", "Tag6", "Tag7", "Tag8", "Tag9", "Tag10"]
keywords: ["news for kids", "kids news", "children's news", "news for tweens", "news for teens", "kid-friendly news", "weekly news for kids", "current events for kids", "world news for children", "educational news", "topic1", "topic2", "topic3", "topic4", "topic5", "topic6", "topic7", "topic8", "topic9", "topic10"]
featured_image: "hero.jpeg"
images: ["hero.jpeg"]
draft: true
enable_rapport: true
podcast:
  enabled: false
  file: "{publication_date}-podcast.mp3"
  duration: 0
  filesize: 0
  shownotes: |
    The Sunday Blender is a weekly newsletter that reports top trending news around the world. It's made for curious English-speaking kids aged 8~15 who aspire for a bigger world and nurture a life-long habit of reading. Every new issue is delivered to your email inbox on Saturday. Each issue comes with 20~25 stories. Each story has no more than 100 words, in plain English with a picture. These stories cover Technology, Global, Economy & Finance, Nature & Environment, Science, Lifestyle & Culture, Sports, History, Art, and Comedy. It's about 10~15 minutes of reading time.

    In the issue of {publication_date}, {description}

    📖 Read the full newsletter article with pictures, comments, and likes:
    https://weekly.sundayblender.com/p/{slug}/

    📧 Subscribe to The Sunday Blender newsletter with email:
    https://weekly.sundayblender.com

    🎧 Listen on:
    • Apple Podcasts: https://podcasts.apple.com/us/podcast/the-sunday-blender-podcast/id1853996806
    • Spotify: https://open.spotify.com/show/0p6Boxgcyy9eJzdBQlu4CG
    • 小宇宙 (Xiaoyuzhou): https://www.xiaoyuzhoufm.com/podcast/691d248b88967822c085fda5
---

## Editor's Words

## Tech

## Global

## Economy & Finance

## Nature & Environment

## Science

## Lifestyle, Entertainment & Culture

## Sports

## This Day in History

## Art of the Week

## Funny
{previous_issues}

---

Thanks for reading! If you enjoy this newsletter, please share it with friends who might also find it interesting and refreshing, if not for themselves, at least for their kids.

'''

    # Write the file
    post_file.write_text(content)

    print()
    print(f"{GREEN}Created:{NC} {post_file}")

    return True

def main():
    print(f"{BLUE}The Sunday Blender - Article Initializer{NC}")
    print(f"{BLUE}{'=' * 45}{NC}")
    print()

    if create_article():
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
