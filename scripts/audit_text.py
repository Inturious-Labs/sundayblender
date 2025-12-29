#!/usr/bin/env python3
"""
Audit a Sunday Blender article to ensure it's ready for publishing.

Usage: Run from within the article folder (content/posts/YYYY/YYYYMMDD/)
       tsb-audit
"""

import sys
import re
from pathlib import Path

# Colors for terminal output
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color

# Constants
WORDS_PER_MINUTE = 200
MAX_READING_TIME_MINUTES = 20
MAX_IMAGE_WIDTH = 1200
MAX_SLUG_LENGTH = 80
MAX_DESCRIPTION_LENGTH = 300
MIN_DESCRIPTION_LENGTH = 50

SECTIONS = [
    "Editor's Words",
    "Tech",
    "Global",
    "Economy & Finance",
    "Nature & Environment",
    "Science",
    "Lifestyle, Entertainment & Culture",
    "Sports",
    "This Day in History",
    "Art of the Week",
    "Funny",
]

def parse_frontmatter(content):
    """Parse YAML frontmatter from markdown content."""
    if not content.startswith('---'):
        return None, content

    parts = content.split('---', 2)
    if len(parts) < 3:
        return None, content

    frontmatter_str = parts[1].strip()
    body = parts[2].strip()

    # Simple YAML parsing for our needs
    frontmatter = {}
    current_key = None
    current_value = []
    in_multiline = False

    for line in frontmatter_str.split('\n'):
        # Check for multiline string continuation
        if in_multiline:
            if line.startswith('    ') or line.strip() == '':
                current_value.append(line)
                continue
            else:
                frontmatter[current_key] = '\n'.join(current_value)
                in_multiline = False

        # Check for new key
        if ':' in line and not line.startswith(' '):
            key, _, value = line.partition(':')
            key = key.strip()
            value = value.strip()

            if value == '|':
                current_key = key
                current_value = []
                in_multiline = True
            elif value.startswith('[') and value.endswith(']'):
                # Parse array
                items = value[1:-1]
                if items:
                    frontmatter[key] = [item.strip().strip('"\'') for item in items.split(',')]
                else:
                    frontmatter[key] = []
            elif value.startswith('"') and value.endswith('"'):
                frontmatter[key] = value[1:-1]
            elif value == 'true':
                frontmatter[key] = True
            elif value == 'false':
                frontmatter[key] = False
            elif value.isdigit():
                frontmatter[key] = int(value)
            else:
                frontmatter[key] = value

    if in_multiline:
        frontmatter[current_key] = '\n'.join(current_value)

    return frontmatter, body


def check_title(frontmatter, errors, warnings):
    """Check title is not placeholder and follows title case."""
    title = frontmatter.get('title', '')

    if not title or title == 'Title Placeholder':
        errors.append("Title is placeholder or empty")
        return

    # Check for reasonable title case (first letter of major words capitalized)
    words = title.split()
    minor_words = {'a', 'an', 'the', 'and', 'but', 'or', 'for', 'nor', 'on', 'at', 'to', 'by', 'in', 'of'}

    for i, word in enumerate(words):
        # Skip words with numbers or special formatting
        if any(c.isdigit() for c in word) or word.startswith('`'):
            continue
        # First word should be capitalized
        if i == 0 and word[0].islower():
            warnings.append(f"Title: first word '{word}' should be capitalized")
        # Major words should be capitalized
        elif word.lower() not in minor_words and word[0].islower() and len(word) > 3:
            warnings.append(f"Title: '{word}' might need capitalization")


def check_slug(frontmatter, errors, warnings):
    """Check slug is valid and reasonable."""
    slug = frontmatter.get('slug', '')

    if not slug or slug.startswith('title-placeholder'):
        errors.append("Slug is placeholder or empty")
        return

    # Check for invalid URL characters
    if not re.match(r'^[a-z0-9-]+$', slug):
        errors.append(f"Slug contains invalid characters: {slug}")

    # Check length
    if len(slug) > MAX_SLUG_LENGTH:
        warnings.append(f"Slug is too long ({len(slug)} chars, max {MAX_SLUG_LENGTH})")


def check_description(frontmatter, errors, warnings):
    """Check description is filled and reasonable length."""
    desc = frontmatter.get('description', '')

    if not desc or 'placeholder' in desc.lower():
        errors.append("Description is placeholder or empty")
        return

    if len(desc) < MIN_DESCRIPTION_LENGTH:
        warnings.append(f"Description is short ({len(desc)} chars, min {MIN_DESCRIPTION_LENGTH})")

    if len(desc) > MAX_DESCRIPTION_LENGTH:
        warnings.append(f"Description is long ({len(desc)} chars, max {MAX_DESCRIPTION_LENGTH})")


def check_tags(frontmatter, errors, warnings):
    """Check tags don't contain placeholders."""
    tags = frontmatter.get('tags', [])

    if not tags:
        errors.append("No tags defined")
        return

    placeholder_tags = [t for t in tags if re.match(r'^Tag\d+$', t)]
    if placeholder_tags:
        errors.append(f"Tag placeholders not replaced: {', '.join(placeholder_tags)}")


def check_keywords(frontmatter, errors, warnings):
    """Check keywords don't contain topic placeholders."""
    keywords = frontmatter.get('keywords', [])

    if not keywords:
        warnings.append("No keywords defined")
        return

    placeholder_keywords = [k for k in keywords if re.match(r'^topic\d+$', k)]
    if placeholder_keywords:
        errors.append(f"Keyword placeholders not replaced: {', '.join(placeholder_keywords)}")


def check_hero_image(cwd, errors, warnings):
    """Check hero image exists and has correct dimensions."""
    hero_jpeg = cwd / "hero.jpeg"
    hero_jpg = cwd / "hero.jpg"

    hero_path = None
    if hero_jpeg.exists():
        hero_path = hero_jpeg
    elif hero_jpg.exists():
        hero_path = hero_jpg

    if not hero_path:
        errors.append("Hero image not found (hero.jpeg or hero.jpg)")
        return

    # Check image dimensions
    try:
        from PIL import Image
        with Image.open(hero_path) as img:
            width, height = img.size
            if width > MAX_IMAGE_WIDTH:
                warnings.append(f"Hero image width ({width}px) exceeds {MAX_IMAGE_WIDTH}px")
    except ImportError:
        warnings.append("PIL not installed, cannot check image dimensions")
    except Exception as e:
        warnings.append(f"Could not read hero image: {e}")


def check_draft_status(frontmatter, errors, warnings):
    """Check draft is still true at this stage."""
    draft = frontmatter.get('draft')

    if draft is not True:
        errors.append("Draft should be 'true' at this stage")


def check_sections(body, errors, warnings):
    """Check all sections have content."""
    for section in SECTIONS:
        # Find section header
        pattern = rf'^##\s+{re.escape(section)}\s*$'
        match = re.search(pattern, body, re.MULTILINE)

        if not match:
            errors.append(f"Section missing: {section}")
            continue

        # Get content until next section or end
        start = match.end()
        next_section = re.search(r'^##\s+', body[start:], re.MULTILINE)

        if next_section:
            section_content = body[start:start + next_section.start()].strip()
        else:
            section_content = body[start:].strip()

        # Remove the "---" separator and "Previous Issues" if at end
        section_content = re.sub(r'^---.*', '', section_content, flags=re.DOTALL).strip()

        if not section_content:
            errors.append(f"Section is empty: {section}")


def check_story_images(body, errors, warnings):
    """Check each story has an image reference.

    Story structure: each story consists of an image followed by a paragraph.
    """
    # Split by section headers
    sections_content = re.split(r'^##\s+', body, flags=re.MULTILINE)[1:]  # Skip content before first ##

    # Collect section stats for table display
    section_stats = []

    for section_block in sections_content:
        lines = section_block.split('\n')
        if not lines:
            continue

        section_name = lines[0].strip()
        section_content = '\n'.join(lines[1:])

        # Skip non-story sections
        if section_name in ["Previous Issues", "Editor's Words"]:
            continue

        # Skip if section is empty (will be caught by check_sections)
        if not section_content.strip() or section_content.strip().startswith('---'):
            continue

        # Count stories by paragraphs (non-empty text blocks that aren't images)
        # Each story = image + paragraph, so we count non-image paragraphs
        paragraphs = re.split(r'\n\s*\n', section_content.strip())
        story_paragraphs = [
            p.strip() for p in paragraphs
            if p.strip() and not p.strip().startswith('![')
        ]

        # Find images in this section
        images = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', section_content)

        num_stories = len(story_paragraphs)
        num_images = len(images)

        # Determine status
        if num_stories == num_images:
            status = f"{GREEN}OK{NC}"
        elif num_stories > num_images:
            status = f"{YELLOW}!{NC}"
            warnings.append(f"Section '{section_name}': {num_stories} stories but only {num_images} images")
        else:
            status = f"{GREEN}OK{NC}"  # More images than stories is fine

        section_stats.append((section_name, num_stories, num_images, status))

    # Print table
    if section_stats:
        print(f"\n{BLUE}Story/Image counts by section:{NC}")
        print(f"{'Section':<35} {'Stories':>8} {'Images':>8} {'Status':>8}")
        print("-" * 63)
        for name, stories, images, status in section_stats:
            # Truncate long section names
            display_name = name[:32] + "..." if len(name) > 35 else name
            print(f"{display_name:<35} {stories:>8} {images:>8} {status:>8}")
        print()


def check_reading_time(body, errors, warnings):
    """Check estimated reading time is within limit."""
    # Count words (rough estimate)
    words = len(re.findall(r'\b\w+\b', body))
    reading_time = words / WORDS_PER_MINUTE

    if reading_time > MAX_READING_TIME_MINUTES:
        errors.append(f"Reading time too long: ~{reading_time:.0f} minutes (max {MAX_READING_TIME_MINUTES})")
    else:
        print(f"{BLUE}Reading time: ~{reading_time:.0f} minutes ({words} words){NC}")


def check_referenced_images(body, cwd, errors, warnings):
    """Check all referenced images exist."""
    images = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', body)

    for alt_text, img_path in images:
        # Skip external URLs
        if img_path.startswith('http://') or img_path.startswith('https://'):
            continue

        # Check if file exists
        img_file = cwd / img_path
        if not img_file.exists():
            errors.append(f"Referenced image not found: {img_path}")


def audit_article():
    """Run all audit checks on the current article."""
    cwd = Path.cwd()
    index_file = cwd / "index.md"

    if not index_file.exists():
        print(f"{RED}Error: index.md not found in current directory{NC}")
        return False

    content = index_file.read_text()
    frontmatter, body = parse_frontmatter(content)

    if not frontmatter:
        print(f"{RED}Error: Could not parse frontmatter{NC}")
        return False

    errors = []
    warnings = []

    print(f"{BLUE}Auditing article...{NC}")
    print()

    # Run all checks
    check_title(frontmatter, errors, warnings)
    check_slug(frontmatter, errors, warnings)
    check_description(frontmatter, errors, warnings)
    check_tags(frontmatter, errors, warnings)
    check_keywords(frontmatter, errors, warnings)
    check_hero_image(cwd, errors, warnings)
    check_draft_status(frontmatter, errors, warnings)
    check_sections(body, errors, warnings)
    check_story_images(body, errors, warnings)
    check_referenced_images(body, cwd, errors, warnings)
    check_reading_time(body, errors, warnings)

    # Print results
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
        print(f"{GREEN}✓ All checks passed!{NC}")
        return True
    elif not errors:
        print(f"{GREEN}✓ No errors, but please review warnings{NC}")
        return True
    else:
        print(f"{RED}✗ Please fix errors before proceeding{NC}")
        return False


def main():
    print(f"{BLUE}The Sunday Blender - Article Audit{NC}")
    print(f"{BLUE}{'=' * 40}{NC}")
    print()

    if audit_article():
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
