"""
Article Parser for The Sunday Blender
Extracts stories from markdown articles for Twitter bot posting.
"""

import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class Story:
    """Represents a single story from an article."""
    section: str
    content: str
    image: Optional[str] = None
    order: int = 0


@dataclass
class Article:
    """Represents a complete Sunday Blender article."""
    title: str
    date: str
    slug: str
    description: str
    tags: List[str]
    featured_image: str
    stories: List[Story]
    url: str


class ArticleParser:
    """Parses Sunday Blender markdown articles and extracts stories."""

    # Sections to exclude from story extraction
    EXCLUDED_SECTIONS = {
        "Editor's Words",
        "Previous Issues",
        "Subscribe"
    }

    def __init__(self, base_url: str = "https://weekly.sundayblender.com"):
        self.base_url = base_url

    def parse_article(self, article_path: Path) -> Article:
        """
        Parse a Sunday Blender article from markdown file.

        Args:
            article_path: Path to the article's index.md file

        Returns:
            Article object with extracted metadata and stories
        """
        content = article_path.read_text(encoding='utf-8')

        # Split frontmatter and body
        parts = content.split('---', 2)
        if len(parts) < 3:
            raise ValueError(f"Invalid article format in {article_path}")

        # Parse frontmatter
        frontmatter = yaml.safe_load(parts[1])
        body = parts[2].strip()

        # Extract stories from body
        stories = self._extract_stories(body, article_path.parent)

        # Build article URL
        slug = frontmatter.get('slug', '')
        article_url = f"{self.base_url}/p/{slug}/"

        return Article(
            title=frontmatter.get('title', ''),
            date=frontmatter.get('date', ''),
            slug=slug,
            description=frontmatter.get('description', ''),
            tags=frontmatter.get('tags', []),
            featured_image=frontmatter.get('featured_image', ''),
            stories=stories,
            url=article_url
        )

    def _extract_stories(self, body: str, article_dir: Path) -> List[Story]:
        """
        Extract individual stories from article body.

        Args:
            body: Article markdown content
            article_dir: Directory containing the article and images

        Returns:
            List of Story objects
        """
        stories = []
        current_section = "Unknown"
        story_order = 0

        # Split by headers (## Section Name)
        sections = re.split(r'^## (.+)$', body, flags=re.MULTILINE)

        # Process sections (odd indices are headers, even are content)
        for i in range(1, len(sections), 2):
            section_name = sections[i].strip()
            section_content = sections[i + 1].strip() if i + 1 < len(sections) else ""

            # Skip excluded sections
            if section_name in self.EXCLUDED_SECTIONS:
                continue

            current_section = section_name

            # Split section into stories (separated by images or double newlines)
            story_blocks = self._split_into_stories(section_content)

            for story_text in story_blocks:
                if not story_text.strip():
                    continue

                # Extract image if present
                image = self._extract_image(story_text, article_dir)

                # Clean up story text (remove image markdown)
                clean_text = re.sub(r'!\[.*?\]\(.*?\)', '', story_text).strip()

                # Skip very short stories (likely not actual stories)
                if len(clean_text) < 50:
                    continue

                stories.append(Story(
                    section=current_section,
                    content=clean_text,
                    image=image,
                    order=story_order
                ))
                story_order += 1

        return stories

    def _split_into_stories(self, section_content: str) -> List[str]:
        """
        Split section content into individual stories.
        Stories are typically separated by images or paragraph breaks.

        Args:
            section_content: Content of a section

        Returns:
            List of story text blocks
        """
        # Split by image markers (each image usually starts a new story)
        image_pattern = r'(?=!\[)'
        parts = re.split(image_pattern, section_content)

        stories = []
        for part in parts:
            if not part.strip():
                continue

            # If part doesn't start with image, it might be multiple paragraphs
            if not part.startswith('!['):
                # Split by double newlines and treat each as a story
                paragraphs = re.split(r'\n\n+', part)
                stories.extend([p.strip() for p in paragraphs if p.strip()])
            else:
                stories.append(part.strip())

        return stories

    def _extract_image(self, story_text: str, article_dir: Path) -> Optional[str]:
        """
        Extract image filename from story text.

        Args:
            story_text: Story markdown text
            article_dir: Directory containing the article

        Returns:
            Absolute path to image file if found, None otherwise
        """
        # Match markdown image syntax: ![alt](filename.jpg)
        match = re.search(r'!\[.*?\]\(([^)]+)\)', story_text)
        if match:
            image_filename = match.group(1)
            image_path = article_dir / image_filename

            if image_path.exists():
                return str(image_path.absolute())

        return None

    def get_latest_article(self, content_dir: Path) -> Optional[Path]:
        """
        Find the most recent published article.

        Args:
            content_dir: Path to content/posts directory

        Returns:
            Path to latest article's index.md, or None if not found
        """
        # Find all index.md files
        article_files = list(content_dir.glob('*/*/*/index.md'))

        if not article_files:
            return None

        # Sort by date (newest first) - relies on YYYY/MM/DDMM directory structure
        article_files.sort(reverse=True)

        # Check each article until we find a non-draft
        for article_file in article_files:
            content = article_file.read_text(encoding='utf-8')
            parts = content.split('---', 2)

            if len(parts) >= 3:
                try:
                    frontmatter = yaml.safe_load(parts[1])
                    # Return first non-draft article
                    if not frontmatter.get('draft', False):
                        return article_file
                except yaml.YAMLError:
                    continue

        return None


def main():
    """Test the article parser."""
    import sys

    if len(sys.argv) > 1:
        article_path = Path(sys.argv[1])
    else:
        # Find latest article
        content_dir = Path(__file__).parent.parent.parent / 'content' / 'posts' / '2025'
        parser = ArticleParser()
        article_path = parser.get_latest_article(content_dir)

        if not article_path:
            print("No articles found!")
            return

        print(f"Using latest article: {article_path}")

    # Parse article
    parser = ArticleParser()
    article = parser.parse_article(article_path)

    # Display results
    print(f"\nTitle: {article.title}")
    print(f"Date: {article.date}")
    print(f"URL: {article.url}")
    print(f"Tags: {', '.join(article.tags)}")
    print(f"\nFound {len(article.stories)} stories:")

    for i, story in enumerate(article.stories, 1):
        print(f"\n{i}. [{story.section}]")
        print(f"   {story.content[:100]}...")
        if story.image:
            print(f"   Image: {Path(story.image).name}")


if __name__ == '__main__':
    main()
