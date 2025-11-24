#!/usr/bin/env python3
"""
Generate enhanced podcast show notes from index.md frontmatter
Adds newsletter URL and subscription links to podcast description
"""

import sys
import re
from pathlib import Path


def read_frontmatter(index_md_path):
    """Extract frontmatter from index.md"""
    with open(index_md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if file starts with frontmatter
    if not content.startswith('---'):
        raise ValueError("No frontmatter found in index.md")

    # Extract frontmatter between --- markers
    parts = content.split('---', 2)
    if len(parts) < 3:
        raise ValueError("Invalid frontmatter format")

    frontmatter = parts[1]
    body = parts[2]

    return frontmatter, body


def parse_frontmatter(frontmatter_text):
    """Parse frontmatter YAML into a dict"""
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

    # Check if podcast is enabled
    podcast_enabled = re.search(r'podcast:\s*\n\s*enabled:\s*true', frontmatter_text, re.MULTILINE)
    data['podcast_enabled'] = bool(podcast_enabled)

    return data


def generate_shownotes(metadata, base_url="https://weekly.sundayblender.com"):
    """Generate enhanced show notes with newsletter links"""

    description = metadata.get('description', 'The Sunday Blender newsletter in audio form.')
    slug = metadata.get('slug', '')

    # Build article URL
    article_url = f"{base_url}/p/{slug}/" if slug else base_url

    # Build show notes
    shownotes = f"""{description}

📖 Read the full newsletter article:
{article_url}

Subscribe to The Sunday Blender newsletter:
{base_url}

🎧 Listen on:
• Apple Podcasts: https://podcasts.apple.com/us/podcast/the-sunday-blender-podcast/id1853996806
• Spotify: https://open.spotify.com/show/0p6Boxgcyy9eJzdBQlu4CG
• 小宇宙 (Xiaoyuzhou): https://www.xiaoyuzhoufm.com/podcast/691d248b88967822c085fda5"""

    return shownotes


def update_frontmatter_with_shownotes(frontmatter_text, shownotes):
    """Add or update podcast_shownotes field in frontmatter"""

    # Check if podcast_shownotes already exists
    if 'podcast_shownotes:' in frontmatter_text:
        # Remove existing podcast_shownotes (multiline)
        frontmatter_text = re.sub(
            r'podcast_shownotes:\s*[|>][-+]?\s*\n(?:(?:\s+.+\n)*)',
            '',
            frontmatter_text
        )

    # Find the podcast section
    podcast_section_match = re.search(r'(podcast:\s*\n(?:\s+.+\n)*)', frontmatter_text)

    if podcast_section_match:
        # Add shownotes to the end of the podcast section
        podcast_section = podcast_section_match.group(1)

        # Determine indentation (usually 2 spaces)
        indent_match = re.search(r'\n(\s+)enabled:', podcast_section)
        indent = indent_match.group(1) if indent_match else '  '

        # Format shownotes as multiline YAML literal
        shownotes_lines = shownotes.split('\n')
        shownotes_yaml = f'{indent}shownotes: |\n'
        for line in shownotes_lines:
            shownotes_yaml += f'{indent}  {line}\n'

        # Insert after the last line of podcast section
        new_podcast_section = podcast_section.rstrip() + '\n' + shownotes_yaml
        frontmatter_text = frontmatter_text.replace(podcast_section, new_podcast_section)

    return frontmatter_text


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
        frontmatter_text, body = read_frontmatter(index_md)

        print("🔍 Parsing frontmatter...")
        metadata = parse_frontmatter(frontmatter_text)

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
        updated_frontmatter = update_frontmatter_with_shownotes(frontmatter_text, shownotes)

        # Write back to file
        updated_content = f"---{updated_frontmatter}---{body}"
        with open(index_md, 'w', encoding='utf-8') as f:
            f.write(updated_content)

        print(f"✅ Success! Updated {index_md}")
        print(f"\n💡 Next steps:")
        print(f"   1. Review the updated index.md")
        print(f"   2. Rebuild your Hugo site")
        print(f"   3. Check the podcast RSS feed at /podcast.xml")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
