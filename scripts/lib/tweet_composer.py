"""
Tweet Composer for The Sunday Blender
Formats stories into tweets with hashtags and optimal text length.
"""

import re
from typing import List, Dict, Optional

try:
    from .article_parser import Story, Article
except ImportError:
    from article_parser import Story, Article


class TweetComposer:
    """Composes tweets from Sunday Blender stories."""

    MAX_TWEET_LENGTH = 280
    MAX_HASHTAGS = 3  # Optimal number for engagement

    # Hashtag mappings for common topics
    HASHTAG_MAP = {
        'ai': '#AI',
        'twitter': '#Twitter',
        'tesla': '#Tesla',
        'space-tech': '#SpaceTech',
        'china': '#China',
        'usa': '#USA',
        'uk': '#UK',
        'japan': '#Japan',
        'nba': '#NBA',
        'soccer': '#Soccer',
        'badminton': '#Badminton',
        'cycling': '#Cycling',
        'climate': '#Climate',
        'science': '#Science',
        'google': '#Google',
        'thailand': '#Thailand',
        'spain': '#Spain',
        'czech': '#Czech',
        'impressionism': '#Art',
        'cursor': '#Tech',
    }

    def __init__(self, article_url: str):
        """
        Initialize tweet composer.

        Args:
            article_url: URL of the article to link back to
        """
        self.article_url = article_url

    def compose_story_tweet(
        self,
        story: Story,
        tags: List[str]
    ) -> Dict[str, str]:
        """
        Compose a single tweet from a story.

        Args:
            story: Story object
            tags: Article tags for hashtag generation

        Returns:
            Dict with 'text' and 'image_path' keys
        """
        # Start with the full story content (no truncation)
        text = story.content

        # Clean up markdown formatting (remove bold, italic, backticks, etc.)
        text = self._clean_markdown(text)

        # Compose final tweet: content + link (no hashtags for now)
        tweet_text = text + f'\n\n{self.article_url}'

        # Check if tweet exceeds limit
        if len(tweet_text) > self.MAX_TWEET_LENGTH:
            # Truncate content smartly to fit
            max_content_length = self.MAX_TWEET_LENGTH - len(f'\n\n{self.article_url}')
            text = self._truncate_smartly(text, max_content_length)
            tweet_text = text + f'\n\n{self.article_url}'

        return {
            'text': tweet_text,
            'image_path': story.image
        }

    def compose_all_tweets(
        self,
        article: Article,
        include_intro_tweet: bool = True
    ) -> List[Dict[str, str]]:
        """
        Compose tweets for all stories in an article.

        Args:
            article: Article object with stories
            include_intro_tweet: Whether to include an intro tweet

        Returns:
            List of tweet dicts with 'text' and 'image_path'
        """
        tweets = []

        # Optional intro tweet
        if include_intro_tweet:
            intro = self._compose_intro_tweet(article)
            tweets.append(intro)

        # Story tweets
        for story in article.stories:
            tweet = self.compose_story_tweet(
                story=story,
                tags=article.tags
            )
            tweets.append(tweet)

        return tweets

    def _compose_intro_tweet(self, article: Article) -> Dict[str, str]:
        """Compose an introductory tweet for the article."""
        text = f"🗞️ New Issue: {article.title}\n\n"
        text += f"{article.description}\n\n"
        text += f"📚 {len(article.stories)} stories this week\n\n"
        text += f"{article.url}"

        # Truncate if needed
        if len(text) > self.MAX_TWEET_LENGTH:
            max_desc_length = self.MAX_TWEET_LENGTH - len(f"🗞️ New Issue: {article.title}\n\n\n\n📚 {len(article.stories)} stories this week\n\n{article.url}")
            description = self._truncate_smartly(article.description, max_desc_length)
            text = f"🗞️ New Issue: {article.title}\n\n"
            text += f"{description}\n\n"
            text += f"📚 {len(article.stories)} stories this week\n\n"
            text += f"{article.url}"

        # Use featured image if available
        image_path = None
        if article.featured_image and article.stories:
            # Try to find featured image path from first story
            first_story = article.stories[0]
            if first_story.image:
                from pathlib import Path
                article_dir = Path(first_story.image).parent
                featured_path = article_dir / article.featured_image
                if featured_path.exists():
                    image_path = str(featured_path)

        return {
            'text': text,
            'image_path': image_path
        }

    def _clean_markdown(self, text: str) -> str:
        """
        Remove markdown formatting from text.

        Args:
            text: Markdown text

        Returns:
            Plain text
        """
        # Remove bold (**text**)
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)

        # Remove italic (*text*)
        text = re.sub(r'\*(.+?)\*', r'\1', text)

        # Remove backticks (`text`)
        text = re.sub(r'`(.+?)`', r'\1', text)

        # Remove links [text](url) -> text
        text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)

        # Clean up multiple spaces
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    def _truncate_smartly(self, text: str, max_length: int) -> str:
        """
        Truncate text at a natural break point.

        Args:
            text: Text to truncate
            max_length: Maximum length

        Returns:
            Truncated text with ellipsis
        """
        if len(text) <= max_length:
            return text

        # Try to truncate at sentence boundary
        truncated = text[:max_length - 3]

        # Find last sentence ending
        sentence_ends = ['.', '!', '?']
        last_sentence = -1

        for char in sentence_ends:
            pos = truncated.rfind(char)
            if pos > last_sentence:
                last_sentence = pos

        if last_sentence > max_length * 0.7:  # At least 70% of desired length
            return truncated[:last_sentence + 1]

        # Otherwise truncate at word boundary
        last_space = truncated.rfind(' ')
        if last_space > 0:
            return truncated[:last_space] + '...'

        # Last resort: hard truncate
        return truncated + '...'

    def _generate_hashtags(
        self,
        tags: List[str],
        section: str,
        content: str
    ) -> List[str]:
        """
        Generate relevant hashtags from article tags.

        Args:
            tags: Article tags
            section: Story section name
            content: Story content

        Returns:
            List of hashtags (max 3)
        """
        hashtags = []

        # Add section-based hashtag
        section_tag = self._section_to_hashtag(section)
        if section_tag:
            hashtags.append(section_tag)

        # Find matching hashtags from tags
        for tag in tags:
            tag_lower = tag.lower()

            # Check if we have a mapping
            if tag_lower in self.HASHTAG_MAP:
                hashtag = self.HASHTAG_MAP[tag_lower]
                if hashtag not in hashtags:
                    hashtags.append(hashtag)

            # Check if tag appears in content (case-insensitive)
            elif tag_lower in content.lower():
                # Convert tag to hashtag format
                hashtag = '#' + tag.replace('-', '').replace(' ', '')
                if hashtag not in hashtags and len(hashtag) > 2:
                    hashtags.append(hashtag)

            if len(hashtags) >= self.MAX_HASHTAGS:
                break

        return hashtags[:self.MAX_HASHTAGS]

    def _section_to_hashtag(self, section: str) -> Optional[str]:
        """Convert section name to hashtag."""
        section_map = {
            'Tech': '#Tech',
            'Global': '#WorldNews',
            'Economy & Finance': '#Economy',
            'Nature & Environment': '#Environment',
            'Science': '#Science',
            'Lifestyle, Entertainment & Culture': '#Culture',
            'Sports': '#Sports',
            'This Day in History': '#History',
            'Art of the Week': '#Art',
            'Funny': '#Humor'
        }

        return section_map.get(section)


def main():
    """Test the tweet composer."""
    from pathlib import Path
    try:
        from .article_parser import ArticleParser
    except ImportError:
        from article_parser import ArticleParser

    # Parse latest article
    content_dir = Path(__file__).parent.parent.parent / 'content' / 'posts' / '2025'
    parser = ArticleParser()
    article_path = parser.get_latest_article(content_dir)

    if not article_path:
        print("No articles found!")
        return

    article = parser.parse_article(article_path)

    # Compose tweets
    composer = TweetComposer(article.url)
    tweets = composer.compose_all_tweets(article, include_intro_tweet=True)

    print(f"Composed {len(tweets)} tweets for: {article.title}\n")

    for i, tweet in enumerate(tweets, 1):
        print(f"{'=' * 60}")
        print(f"Tweet {i}:")
        print(f"{'=' * 60}")
        print(tweet['text'])
        print(f"\nLength: {len(tweet['text'])} chars")
        if tweet['image_path']:
            print(f"Image: {Path(tweet['image_path']).name}")
        print()


if __name__ == '__main__':
    main()
