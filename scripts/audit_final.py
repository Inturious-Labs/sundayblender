#!/usr/bin/env python3
"""
Final audit for Sunday Blender article before git push.
Checks HTML output, RSS feeds, and Twitter card metadata.

Usage: Run from within the article folder (content/posts/YYYY/YYYYMMDD/)
       tsb-audit-final
"""

import sys
import re
from pathlib import Path
from datetime import datetime

# Colors for terminal output
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'


def get_repo_root():
    """Find the repo root by looking for hugo.toml."""
    cwd = Path.cwd()
    for parent in [cwd] + list(cwd.parents):
        if (parent / "hugo.toml").exists():
            return parent
    return None


def parse_frontmatter(content):
    """Parse frontmatter from markdown content."""
    if not content.startswith('---'):
        return None
    parts = content.split('---', 2)
    if len(parts) < 3:
        return None
    return parts[1]


def extract_field(frontmatter, field):
    """Extract a field value from frontmatter."""
    pattern = rf'^{field}:\s*["\']?(.*?)["\']?\s*$'
    match = re.search(pattern, frontmatter, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return ""


def check_draft_status(frontmatter, errors, warnings, passed):
    """Check draft is set to false."""
    draft_match = re.search(r'^draft:\s*(true|false)', frontmatter, re.MULTILINE)
    if draft_match:
        if draft_match.group(1) == 'true':
            errors.append("draft is still 'true' - change to 'false' before publishing")
        else:
            passed.append("draft is set to 'false'")
    else:
        warnings.append("draft field not found in frontmatter")


def check_twitter_card(html_path, errors, warnings, passed):
    """Check Twitter card meta tags in HTML."""
    if not html_path.exists():
        errors.append(f"HTML file not found: {html_path}")
        return

    content = html_path.read_text()

    # Check for twitter:card meta tag
    card_match = re.search(r'<meta\s+(?:name|property)=["\']twitter:card["\']\s+content=["\']([^"\']+)["\']', content)
    if not card_match:
        card_match = re.search(r'<meta\s+content=["\']([^"\']+)["\']\s+(?:name|property)=["\']twitter:card["\']', content)

    if card_match:
        card_type = card_match.group(1)
        if card_type != 'summary_large_image':
            warnings.append(f"Twitter card is '{card_type}', expected 'summary_large_image'")
        else:
            passed.append("Twitter card is 'summary_large_image'")
    else:
        errors.append("Twitter card meta tag not found")

    # Check for twitter:image meta tag
    image_match = re.search(r'<meta\s+(?:name|property)=["\']twitter:image["\']\s+content=["\']([^"\']+)["\']', content)
    if not image_match:
        image_match = re.search(r'<meta\s+content=["\']([^"\']+)["\']\s+(?:name|property)=["\']twitter:image["\']', content)

    if image_match:
        image_url = image_match.group(1)
        if not image_url or image_url == '':
            errors.append("Twitter image URL is empty")
        else:
            passed.append("Twitter image URL is set")
    else:
        errors.append("Twitter image meta tag not found")

    # Check og:image as well
    og_image_match = re.search(r'<meta\s+(?:name|property)=["\']og:image["\']\s+content=["\']([^"\']+)["\']', content)
    if not og_image_match:
        og_image_match = re.search(r'<meta\s+content=["\']([^"\']+)["\']\s+(?:name|property)=["\']og:image["\']', content)

    if not og_image_match:
        warnings.append("og:image meta tag not found")
    else:
        passed.append("og:image meta tag is set")


def check_main_rss(repo_root, slug, date_str, errors, warnings, passed):
    """Check main RSS feed includes the article."""
    rss_path = repo_root / "public" / "index.xml"

    if not rss_path.exists():
        errors.append("Main RSS feed (index.xml) not found - run 'hugo' first")
        return

    content = rss_path.read_text()

    # Check if the article slug appears in the RSS
    if slug and slug not in content:
        errors.append(f"Article '{slug}' not found in main RSS feed")
    else:
        passed.append("Article found in main RSS feed")
        # Also check the date
        if date_str and date_str in content:
            passed.append("Article date found in RSS feed")
        else:
            warnings.append("Article date not found in RSS - may be expected if date format differs")


def check_podcast_rss(repo_root, slug, date_str, errors, warnings, passed):
    """Check podcast RSS feed includes the episode."""
    podcast_rss_path = repo_root / "public" / "podcast.xml"

    if not podcast_rss_path.exists():
        errors.append("Podcast RSS feed (podcast.xml) not found - run 'hugo' first")
        return

    content = podcast_rss_path.read_text()

    # Check if the article slug appears in the podcast RSS
    if slug and slug not in content:
        errors.append(f"Episode '{slug}' not found in podcast RSS feed")
    else:
        passed.append("Episode found in podcast RSS feed")

    # Check for enclosure tag (mp3 file)
    if '<enclosure' not in content:
        errors.append("No podcast enclosure found in RSS feed")
    else:
        passed.append("Podcast enclosure tag found in RSS")

    # Check for the specific episode's mp3
    mp3_filename = f"{date_str}-podcast.mp3"
    if mp3_filename not in content:
        warnings.append(f"MP3 file '{mp3_filename}' not found in podcast RSS")
    else:
        passed.append(f"MP3 file '{mp3_filename}' found in podcast RSS")


def check_pdf_exists(cwd, date_str, errors, warnings, passed):
    """Check PDF file exists."""
    pdf_files = list(cwd.glob("*.pdf"))
    if not pdf_files:
        errors.append("No PDF file found in article folder")
    else:
        passed.append(f"PDF file found: {pdf_files[0].name}")


def check_mp3_exists(cwd, date_str, errors, warnings, passed):
    """Check MP3 file exists."""
    mp3_filename = f"{date_str}-podcast.mp3"
    mp3_path = cwd / mp3_filename

    if not mp3_path.exists():
        errors.append(f"MP3 file not found: {mp3_filename}")
    else:
        passed.append(f"MP3 file found: {mp3_filename}")


def check_podcast_frontmatter(frontmatter, errors, warnings, passed):
    """Check podcast section in frontmatter is properly configured."""
    if 'podcast:' not in frontmatter:
        errors.append("podcast section not found in frontmatter")
        return

    # Check enabled
    enabled_match = re.search(r'enabled:\s*(true|false)', frontmatter)
    if enabled_match:
        if enabled_match.group(1) != 'true':
            errors.append("podcast.enabled is not 'true'")
        else:
            passed.append("podcast.enabled is 'true'")
    else:
        errors.append("podcast.enabled field not found")

    # Check duration
    duration_match = re.search(r'duration:\s*(\d+)', frontmatter)
    if duration_match:
        duration = int(duration_match.group(1))
        if duration == 0:
            errors.append("podcast.duration is 0 - run tsb-make-podcast")
        else:
            passed.append(f"podcast.duration is set ({duration}s)")
    else:
        errors.append("podcast.duration not found")

    # Check filesize
    filesize_match = re.search(r'filesize:\s*(\d+)', frontmatter)
    if filesize_match:
        filesize = int(filesize_match.group(1))
        if filesize == 0:
            errors.append("podcast.filesize is 0 - run tsb-make-podcast")
        else:
            passed.append(f"podcast.filesize is set ({filesize} bytes)")
    else:
        errors.append("podcast.filesize not found")


def check_hero_image_in_html(html_path, errors, warnings, passed):
    """Check hero image is properly displayed in HTML."""
    if not html_path.exists():
        return

    content = html_path.read_text()

    # Check for hero image
    if 'hero.jpeg' not in content and 'hero.jpg' not in content:
        warnings.append("Hero image reference not found in HTML")
    else:
        passed.append("Hero image found in HTML")


def main():
    cwd = Path.cwd()
    index_file = cwd / "index.md"

    print(f"{BLUE}🔍 Sunday Blender Final Audit{NC}")
    print(f"{BLUE}{'━' * 40}{NC}")
    print()

    # Check index.md exists
    if not index_file.exists():
        print(f"{RED}❌ Error: index.md not found{NC}")
        sys.exit(1)

    # Read and parse frontmatter
    content = index_file.read_text()
    frontmatter = parse_frontmatter(content)

    if not frontmatter:
        print(f"{RED}❌ Error: Could not parse frontmatter{NC}")
        sys.exit(1)

    # Extract fields
    date_str = extract_field(frontmatter, 'date')
    slug = extract_field(frontmatter, 'slug')

    print(f"{BLUE}Article: {slug}{NC}")
    print(f"{BLUE}Date: {date_str}{NC}")
    print()

    # Find repo root and HTML file
    repo_root = get_repo_root()
    if not repo_root:
        print(f"{RED}❌ Error: Could not find repo root{NC}")
        sys.exit(1)

    html_path = repo_root / "public" / "p" / slug / "index.html"

    errors = []
    warnings = []
    passed = []

    # Run all checks
    check_draft_status(frontmatter, errors, warnings, passed)
    check_pdf_exists(cwd, date_str, errors, warnings, passed)
    check_mp3_exists(cwd, date_str, errors, warnings, passed)
    check_podcast_frontmatter(frontmatter, errors, warnings, passed)
    check_twitter_card(html_path, errors, warnings, passed)
    check_hero_image_in_html(html_path, errors, warnings, passed)
    check_main_rss(repo_root, slug, date_str, errors, warnings, passed)
    check_podcast_rss(repo_root, slug, date_str, errors, warnings, passed)

    # Print results - passed checks first
    if passed:
        print(f"{GREEN}Passed ({len(passed)}):{NC}")
        for item in passed:
            print(f"  {GREEN}✓{NC} {item}")
        print()

    if errors:
        print(f"{RED}Errors ({len(errors)}):{NC}")
        for error in errors:
            print(f"  {RED}✗{NC} {error}")
        print()

    if warnings:
        print(f"{YELLOW}Warnings ({len(warnings)}):{NC}")
        for warning in warnings:
            print(f"  {YELLOW}⚠{NC} {warning}")
        print()

    if not errors and not warnings:
        print(f"{GREEN}✓ All checks passed! Ready for git push.{NC}")
        return True
    elif not errors:
        print(f"{GREEN}✓ No errors. Review warnings, then proceed with git push.{NC}")
        return True
    else:
        print(f"{RED}✗ Please fix errors before git push{NC}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
