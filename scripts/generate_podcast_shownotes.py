#!/usr/bin/env python3
"""
Generate enhanced podcast show notes from index.md frontmatter
Adds newsletter URL and subscription links to podcast description
No external dependencies required
"""

import sys
import re
from pathlib import Path


def read_markdown_with_frontmatter(index_md_path):
    """Extract frontmatter and body from index.md"""
    with open(index_md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if file starts with frontmatter
    if not content.startswith('---'):
        raise ValueError("No frontmatter found in index.md")

    # Extract frontmatter between --- markers
    parts = content.split('---', 2)
    if len(parts) < 3:
        raise ValueError("Invalid frontmatter format")

    frontmatter_text = parts[1]
    body = parts[2]

    return frontmatter_text, body


def parse_simple_fields(frontmatter_text):
    """Extract simple fields from frontmatter"""
    data = {}

    # Extract title
    title_match = re.search(r'^title:\s*["\']?(.*?)["\']?\s*$', frontmatter_text, re.MULTILINE)
    if title_match:
        data['title'] = title_match.group(1).strip()

    # Extract slug
    slug_match = re.search(r'^slug:\s*(.+?)\s*$', frontmatter_text, re.MULTILINE)
    if slug_match:
        data['slug'] = slug_match.group(1).strip()

    # Extract description
    desc_match = re.search(r'^description:\s*["\']?(.*?)["\']?\s*$', frontmatter_text, re.MULTILINE)
    if desc_match:
        data['description'] = desc_match.group(1).strip()

    # Extract date
    date_match = re.search(r'^date:\s*(.+?)\s*$', frontmatter_text, re.MULTILINE)
    if date_match:
        data['date'] = date_match.group(1).strip()

    # Extract reading time (if available)
    reading_time_match = re.search(r'^readingTime:\s*(\d+)\s*$', frontmatter_text, re.MULTILINE)
    if reading_time_match:
        data['reading_time'] = reading_time_match.group(1).strip()

    # Check if podcast is enabled
    podcast_enabled = re.search(r'podcast:\s*\n\s+enabled:\s*true', frontmatter_text, re.MULTILINE)
    data['podcast_enabled'] = bool(podcast_enabled)

    return data


def generate_shownotes(metadata, base_url="https://weekly.sundayblender.com"):
    """Generate enhanced show notes with newsletter links"""
    from datetime import datetime

    description = metadata.get('description', 'The Sunday Blender newsletter in audio form.')
    slug = metadata.get('slug', '')
    reading_time = metadata.get('reading_time')
    date_str = metadata.get('date', '')

    # Build article URL
    article_url = f"{base_url}/p/{slug}/" if slug else base_url

    # Format date for transition paragraph
    transition = ""
    if date_str:
        try:
            # Parse date (format: 2025-11-22 or YYYY-MM-DD)
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            # Format as "Nov 22"
            formatted_date = date_obj.strftime('%b %d')
            transition = f"In the issue of {formatted_date}, "
        except ValueError:
            transition = ""

    # Build show notes with newsletter description
    newsletter_description = "The Sunday Blender is a weekly newsletter that reports top trending news around the world. It's made for curious English-speaking kids aged 8~15 who aspire for a bigger world and nurture a life-long habit of reading. Every new issue is delivered to your email inbox on Saturday. Each issue comes with 20~25 stories. Each story has no more than 100 words, in plain English with a picture. These stories cover Technology, Global, Economy & Finance, Nature & Environment, Science, Lifestyle & Culture, Sports, History, Art, and Comedy. It's about 10~15 minutes of reading time."

    shownotes = f"""{newsletter_description}

{transition}{description}"""

    # Add reading time if available
    if reading_time:
        shownotes += f"\n\n⏱️  Reading time: {reading_time} minutes"

    shownotes += f"""

📖 Read the full newsletter article with pictures, comments, and likes:
{article_url}

📧 Subscribe to The Sunday Blender newsletter with email:
{base_url}

🎧 Listen on:
• Apple Podcasts: https://podcasts.apple.com/us/podcast/the-sunday-blender-podcast/id1853996806
• Spotify: https://open.spotify.com/show/0p6Boxgcyy9eJzdBQlu4CG
• 小宇宙 (Xiaoyuzhou): https://www.xiaoyuzhoufm.com/podcast/691d248b88967822c085fda5"""

    return shownotes


def update_podcast_shownotes(frontmatter_text, shownotes):
    """Update or add shownotes field in podcast section"""

    # First, remove any existing shownotes in the podcast section
    # This pattern matches "  shownotes: |" and all subsequent indented lines
    # It stops when it hits a line that starts with 0-2 spaces followed by a word character or end of string
    pattern = r'\n  shownotes:\s*\|[^\n]*(?:\n    [^\n]*)*'
    frontmatter_text = re.sub(pattern, '', frontmatter_text)

    # Find the podcast section
    podcast_match = re.search(r'^(podcast:\s*\n)((?:\s+.+\n)*)', frontmatter_text, re.MULTILINE)

    if not podcast_match:
        raise ValueError("No podcast section found in frontmatter")

    # Get the indentation used in the podcast section (usually 2 spaces)
    podcast_content = podcast_match.group(2)
    indent_match = re.search(r'^(\s+)', podcast_content, re.MULTILINE)
    indent = indent_match.group(1) if indent_match else '  '

    # Format shownotes as YAML multiline string
    shownotes_lines = shownotes.split('\n')
    shownotes_yaml = f'{indent}shownotes: |\n'
    for line in shownotes_lines:
        shownotes_yaml += f'{indent}  {line}\n'

    # Find where to insert (at the end of the podcast section)
    # The podcast section ends when we hit a line that's not indented or is a new top-level key
    podcast_end = podcast_match.end()

    # Insert the shownotes at the end of the podcast section
    result = frontmatter_text[:podcast_end].rstrip() + '\n' + shownotes_yaml + frontmatter_text[podcast_end:]

    return result


def write_markdown_with_frontmatter(index_md_path, frontmatter_text, body):
    """Write frontmatter and body back to index.md"""
    with open(index_md_path, 'w', encoding='utf-8') as f:
        f.write('---')
        f.write(frontmatter_text)
        f.write('---')
        f.write(body)


def main():
    """Main function"""
    if len(sys.argv) > 1:
        working_dir = Path(sys.argv[1])
    else:
        working_dir = Path.cwd()

    index_md = working_dir / "index.md"

    if not index_md.exists():
        print(f"❌ Error: index.md not found in {working_dir}")
        sys.exit(1)

    try:
        print("📖 Reading index.md...")
        frontmatter_text, body = read_markdown_with_frontmatter(index_md)

        print("🔍 Parsing frontmatter...")
        metadata = parse_simple_fields(frontmatter_text)

        if not metadata.get('podcast_enabled'):
            print("⚠️  Warning: podcast.enabled is not true in frontmatter")
            print("Skipping show notes generation.")
            sys.exit(0)

        print("✍️  Generating show notes...")
        shownotes = generate_shownotes(metadata)

        print("\n" + "="*60)
        print("GENERATED SHOW NOTES:")
        print("="*60)
        print(shownotes)
        print("="*60 + "\n")

        print("📝 Updating frontmatter...")
        updated_frontmatter = update_podcast_shownotes(frontmatter_text, shownotes)

        write_markdown_with_frontmatter(index_md, updated_frontmatter, body)

        print(f"✅ Success! Updated {index_md}")
        print(f"\n💡 Next steps:")
        print(f"   1. Review the updated index.md")
        print(f"   2. Rebuild your Hugo site")
        print(f"   3. Check the podcast RSS feed at /podcast.xml")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
