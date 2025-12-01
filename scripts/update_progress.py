#!/usr/bin/env python3
"""
Update Content Update Progress chart in README.md.
Checks production site and podcast platforms for article status.

Usage: Run from repo root
       tsb-update-progress [--date YYYY-MM-DD] [--all]

Options:
  --date YYYY-MM-DD  Check specific article date
  --all              Check all articles in the table
  (no args)          Check only the most recent article
"""

import sys
import re
import argparse
import urllib.request
import urllib.error
import ssl
from pathlib import Path
from datetime import datetime

# Colors for terminal output
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'

BASE_URL = "https://weekly.sundayblender.com"
PODCAST_RSS = f"{BASE_URL}/podcast.xml"
APPLE_PODCASTS = "https://podcasts.apple.com/us/podcast/the-sunday-blender-podcast/id1853996806"
SPOTIFY = "https://open.spotify.com/show/0p6Boxgcyy9eJzdBQlu4CG"
XIAOYUZHOU = "https://www.xiaoyuzhoufm.com/podcast/691d248b88967822c085fda5"


def get_repo_root():
    """Find the repo root by looking for hugo.toml."""
    cwd = Path.cwd()
    for parent in [cwd] + list(cwd.parents):
        if (parent / "hugo.toml").exists():
            return parent
    return None


def fetch_url(url, timeout=30):
    """Fetch URL content with proper headers."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }

    # Create SSL context that doesn't verify (for some podcast platforms)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as response:
            return response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        return None


def extract_slug_from_url(url):
    """Extract slug from article URL."""
    match = re.search(r'/p/([^/]+)/?$', url)
    if match:
        return match.group(1)
    return None


def check_images(html_content):
    """Check if article has images properly displayed."""
    if not html_content:
        return False

    # Look for article images - handle both quoted and minified (unquoted) HTML
    # Pattern 1: src="url.jpg" or src='url.jpg'
    # Pattern 2: src=url.jpg (minified)
    jpg_files = re.findall(r'\.jpe?g', html_content, re.IGNORECASE)
    png_files = re.findall(r'\.png', html_content, re.IGNORECASE)

    # Count image files (excluding common non-content images)
    all_images = re.findall(r'[^"\'\s>]+\.(?:jpg|jpeg|png)', html_content, re.IGNORECASE)
    content_images = [img for img in all_images if
                      not any(x in img.lower() for x in ['icon', 'logo', 'favicon', 'avatar', 'ic_logo'])]

    return len(content_images) >= 3  # Article should have multiple images


def check_pdf(html_content):
    """Check if PDF download link exists."""
    if not html_content:
        return False

    # Look for PDF link - handle both quoted and minified HTML
    # Pattern matches: href="...pdf" or href=...pdf (minified)
    return bool(re.search(r'\.pdf', html_content, re.IGNORECASE))


def check_inline_audio(html_content):
    """Check if inline audio player exists."""
    if not html_content:
        return False

    # Look for audio player indicators - handle minified HTML
    audio_indicators = [
        r'<audio',
        r'podcast-player',
        r'audio-player',
        r'Listen to this article',
        r'\.mp3',  # Simple mp3 file reference
    ]

    for pattern in audio_indicators:
        if re.search(pattern, html_content, re.IGNORECASE):
            return True

    return False


def check_shownotes_in_rss(rss_content, slug):
    """Check if episode has shownotes in podcast RSS."""
    if not rss_content or not slug:
        return False

    # Find the item containing this slug
    items = re.findall(r'<item>(.*?)</item>', rss_content, re.DOTALL)

    for item in items:
        if slug in item:
            # Check for description with actual content (not just boilerplate)
            desc_match = re.search(r'<description>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</description>', item, re.DOTALL)
            if desc_match:
                desc = desc_match.group(1)
                # Shownotes should be substantial (more than just a few words)
                return len(desc.strip()) > 200

    return False


# Cache for podcast platform pages (fetched once)
_platform_cache = {}


def get_platform_content(platform_name, url):
    """Get cached platform content or fetch it."""
    if platform_name not in _platform_cache:
        _platform_cache[platform_name] = fetch_url(url)
    return _platform_cache[platform_name]


def get_platform_episode_dates(platform_name, url):
    """Extract episode dates from a podcast platform page."""
    content = get_platform_content(platform_name, url)
    if not content:
        return set()

    dates = set()

    # Look for dates in various formats
    # Format: 2025-11-29, Nov 29, November 29, etc.
    iso_dates = re.findall(r'2025-\d{2}-\d{2}', content)
    dates.update(iso_dates)

    # Format: "datePublished":"2025-11-29T..." (JSON-LD)
    json_dates = re.findall(r'"datePublished":\s*"(\d{4}-\d{2}-\d{2})', content)
    dates.update(json_dates)

    return dates


# Cache for episode dates per platform
_episode_dates_cache = {}


def get_cached_episode_dates(platform_name, url):
    """Get cached episode dates for a platform."""
    if platform_name not in _episode_dates_cache:
        _episode_dates_cache[platform_name] = get_platform_episode_dates(platform_name, url)
    return _episode_dates_cache[platform_name]


def check_apple_podcasts(date_str):
    """Check if episode exists on Apple Podcasts by date."""
    dates = get_cached_episode_dates('apple', APPLE_PODCASTS)
    return date_str in dates if dates else None


def check_spotify(date_str):
    """Check if episode exists on Spotify (uses Apple dates as proxy - same RSS feed)."""
    # Spotify and Apple both pull from same RSS, so use Apple's detected dates
    dates = get_cached_episode_dates('apple', APPLE_PODCASTS)
    return date_str in dates if dates else None


def check_xiaoyuzhou(date_str):
    """Check if episode exists on Xiaoyuzhou - requires manual verification."""
    # Xiaoyuzhou is manually uploaded, can't reliably auto-detect
    return None  # Always return None (unknown) for manual check


def get_article_title(html_content):
    """Extract article title from HTML."""
    if html_content:
        title_match = re.search(r'<title>([^<]+)</title>', html_content)
        if title_match:
            return title_match.group(1).strip()
    return None


def check_article(date_str, url, rss_content):
    """Check all aspects of an article and return status dict."""
    slug = extract_slug_from_url(url)

    print(f"\n{BLUE}Checking {date_str}: {slug}{NC}")

    # Fetch article HTML
    html_content = fetch_url(url)
    if not html_content:
        print(f"  {RED}✗ Could not fetch article{NC}")
        return None

    # Get article title for platform matching
    title = get_article_title(html_content)

    results = {}

    # Check Images
    results['images'] = check_images(html_content)
    status = f"{GREEN}✓{NC}" if results['images'] else f"{RED}✗{NC}"
    print(f"  {status} Images")

    # Check PDF
    results['pdf'] = check_pdf(html_content)
    status = f"{GREEN}✓{NC}" if results['pdf'] else f"{RED}✗{NC}"
    print(f"  {status} PDF")

    # Check Show Notes (from RSS)
    results['shownotes'] = check_shownotes_in_rss(rss_content, slug)
    status = f"{GREEN}✓{NC}" if results['shownotes'] else f"{RED}✗{NC}"
    print(f"  {status} Show Notes")

    # Check Apple Podcasts (by date)
    results['apple'] = check_apple_podcasts(date_str)
    if results['apple'] is None:
        status = f"{YELLOW}?{NC}"
    else:
        status = f"{GREEN}✓{NC}" if results['apple'] else f"{RED}✗{NC}"
    print(f"  {status} Apple Podcasts")

    # Check Spotify (by date)
    results['spotify'] = check_spotify(date_str)
    if results['spotify'] is None:
        status = f"{YELLOW}?{NC}"
    else:
        status = f"{GREEN}✓{NC}" if results['spotify'] else f"{RED}✗{NC}"
    print(f"  {status} Spotify")

    # Check Xiaoyuzhou (by date)
    results['xiaoyuzhou'] = check_xiaoyuzhou(date_str)
    if results['xiaoyuzhou'] is None:
        status = f"{YELLOW}?{NC}"
    else:
        status = f"{GREEN}✓{NC}" if results['xiaoyuzhou'] else f"{RED}✗{NC}"
    print(f"  {status} 小宇宙")

    # Check Inline Audio
    results['inline'] = check_inline_audio(html_content)
    status = f"{GREEN}✓{NC}" if results['inline'] else f"{RED}✗{NC}"
    print(f"  {status} Inline 🎧")

    # Ximalaya - manual check (placeholder)
    results['ximalaya'] = None  # Cannot auto-check
    print(f"  {YELLOW}?{NC} 喜马拉雅 (manual)")

    return results


def parse_readme_table(readme_content):
    """Parse the progress table from README and return list of (date, url, line_num)."""
    articles = []

    lines = readme_content.split('\n')
    in_table = False
    header_line = None
    separator_line = None

    for i, line in enumerate(lines):
        if '| Date |' in line:
            in_table = True
            header_line = i
            continue

        if in_table and header_line is not None and separator_line is None and line.startswith('|--'):
            separator_line = i
            continue

        if in_table and line.startswith('|'):
            # Parse table row
            match = re.search(r'\[(\d{4}-\d{2}-\d{2})\]\((https://[^)]+)\)', line)
            if match:
                date_str = match.group(1)
                url = match.group(2)
                articles.append((date_str, url, i))
        elif in_table and not line.startswith('|'):
            break

    return articles, separator_line


def get_published_articles_from_rss(rss_content):
    """Extract all published articles from RSS feed."""
    if not rss_content:
        return []

    articles = []
    items = re.findall(r'<item>(.*?)</item>', rss_content, re.DOTALL)

    for item in items:
        # Extract link
        link_match = re.search(r'<link>([^<]+)</link>', item)
        if not link_match:
            continue
        url = link_match.group(1).strip()

        # Extract pubDate
        date_match = re.search(r'<pubDate>([^<]+)</pubDate>', item)
        if not date_match:
            continue

        # Parse date - format: "Sat, 29 Nov 2025 00:00:00 +0000"
        try:
            date_str = date_match.group(1).strip()
            # Parse RFC 2822 date
            date_obj = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %z')
            date_formatted = date_obj.strftime('%Y-%m-%d')
        except:
            continue

        articles.append((date_formatted, url))

    return articles


def add_missing_articles(readme_content, rss_articles, existing_dates, separator_line):
    """Add new articles from RSS that aren't in the README table."""
    lines = readme_content.split('\n')
    new_rows = []

    for date_str, url in rss_articles:
        if date_str not in existing_dates:
            # Create new row with empty status
            new_row = f"| [{date_str}]({url}) |  |  |  |  |  |  |  |  |"
            new_rows.append((date_str, new_row))

    if not new_rows:
        return readme_content, []

    # Sort by date (newest first)
    new_rows.sort(key=lambda x: x[0], reverse=True)

    # Insert after separator line
    insert_pos = separator_line + 1
    for date_str, row in new_rows:
        lines.insert(insert_pos, row)

    return '\n'.join(lines), [r[0] for r in new_rows]


def update_readme_row(line, results):
    """Update a README table row with new results."""
    # Extract existing parts
    match = re.match(r'(\| \[[^\]]+\]\([^)]+\) \|)', line)
    if not match:
        return line

    prefix = match.group(1)

    def status_emoji(val):
        if val is None:
            return ''  # Keep empty for manual
        return '🟢' if val else '🔴'

    # Build new row
    # | Date | Images | PDF | Show Notes | Apple | Spotify | 小宇宙 | 喜马拉雅 | Inline 🎧 |
    new_row = (
        f"{prefix} "
        f"{status_emoji(results.get('images'))} | "
        f"{status_emoji(results.get('pdf'))} | "
        f"{status_emoji(results.get('shownotes'))} | "
        f"{status_emoji(results.get('apple'))} | "
        f"{status_emoji(results.get('spotify'))} | "
        f"{status_emoji(results.get('xiaoyuzhou'))} | "
        f"{status_emoji(results.get('ximalaya'))} | "
        f"{status_emoji(results.get('inline'))} |"
    )

    return new_row


def main():
    parser = argparse.ArgumentParser(description='Update Content Update Progress chart')
    parser.add_argument('--date', help='Check specific article date (YYYY-MM-DD)')
    parser.add_argument('--all', action='store_true', help='Check all articles in table')
    parser.add_argument('--dry-run', action='store_true', help='Show results without updating README')
    parser.add_argument('--sync', action='store_true', help='Add new articles from production RSS')
    args = parser.parse_args()

    print(f"{BLUE}📊 Sunday Blender Progress Checker{NC}")
    print(f"{BLUE}{'━' * 40}{NC}")

    # Find repo root
    repo_root = get_repo_root()
    if not repo_root:
        print(f"{RED}❌ Error: Could not find repo root{NC}")
        sys.exit(1)

    readme_path = repo_root / "README.md"
    if not readme_path.exists():
        print(f"{RED}❌ Error: README.md not found{NC}")
        sys.exit(1)

    readme_content = readme_path.read_text()

    # Fetch main RSS to discover all articles
    print(f"\n{BLUE}Fetching main RSS feed...{NC}")
    main_rss_url = f"{BASE_URL}/index.xml"
    main_rss_content = fetch_url(main_rss_url)
    if not main_rss_content:
        print(f"{YELLOW}⚠ Could not fetch main RSS{NC}")

    # Parse existing table
    articles, separator_line = parse_readme_table(readme_content)
    if not articles and separator_line is None:
        print(f"{RED}❌ Error: Could not parse progress table{NC}")
        sys.exit(1)

    print(f"{GREEN}Found {len(articles)} articles in progress table{NC}")

    # Check for new articles from RSS and add them
    existing_dates = {a[0] for a in articles}
    rss_articles = get_published_articles_from_rss(main_rss_content)
    new_articles = [(d, u) for d, u in rss_articles if d not in existing_dates]

    if new_articles:
        print(f"{GREEN}Found {len(new_articles)} new articles to add{NC}")
        for date_str, url in sorted(new_articles, reverse=True):
            print(f"  + {date_str}")

        if not args.dry_run:
            readme_content, added_dates = add_missing_articles(
                readme_content, rss_articles, existing_dates, separator_line
            )
            # Re-parse after adding new rows
            articles, separator_line = parse_readme_table(readme_content)
            print(f"{GREEN}✓ Added {len(added_dates)} new articles to table{NC}")

    # Fetch podcast RSS for shownotes check
    print(f"\n{BLUE}Fetching podcast RSS...{NC}")
    podcast_rss_content = fetch_url(PODCAST_RSS)
    if not podcast_rss_content:
        print(f"{YELLOW}⚠ Could not fetch podcast RSS{NC}")

    # If --sync only, just add new articles without checking status
    if args.sync and not args.date and not args.all:
        if not args.dry_run and new_articles:
            readme_path.write_text(readme_content)
            print(f"\n{GREEN}✓ README.md updated with new articles{NC}")
        print(f"\n{GREEN}{'━' * 40}{NC}")
        print(f"{GREEN}✅ Sync complete!{NC}")
        return

    # Determine which articles to check
    if args.date:
        # Check specific date
        articles_to_check = [(d, u, l) for d, u, l in articles if d == args.date]
        if not articles_to_check:
            print(f"{RED}❌ Error: Date {args.date} not found in table{NC}")
            sys.exit(1)
    elif args.all:
        # Check all articles
        articles_to_check = articles
    else:
        # Check only most recent (first in table)
        articles_to_check = articles[:1]

    # Check articles and collect results
    all_results = {}
    for date_str, url, line_num in articles_to_check:
        results = check_article(date_str, url, podcast_rss_content)
        if results:
            all_results[(date_str, line_num)] = results

    if not all_results and not new_articles:
        print(f"\n{YELLOW}No results to update{NC}")
        sys.exit(0)

    # Update README
    if args.dry_run:
        print(f"\n{YELLOW}Dry run - not updating README{NC}")
    else:
        print(f"\n{BLUE}Updating README.md...{NC}")
        lines = readme_content.split('\n')

        for (date_str, line_num), results in all_results.items():
            lines[line_num] = update_readme_row(lines[line_num], results)

        readme_path.write_text('\n'.join(lines))
        print(f"{GREEN}✓ README.md updated{NC}")

    print(f"\n{GREEN}{'━' * 40}{NC}")
    print(f"{GREEN}✅ Progress check complete!{NC}")


if __name__ == "__main__":
    main()
