#!/usr/bin/env python3
"""
Schedule tweets from a Sunday Blender article.
Called by schedule_tweets.sh
"""

import sys
from pathlib import Path
from datetime import datetime

# Import modules
try:
    from article_parser import ArticleParser
    from tweet_composer import TweetComposer
    from tweet_queue import TweetQueue, generate_schedule
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from article_parser import ArticleParser
    from tweet_composer import TweetComposer
    from tweet_queue import TweetQueue, generate_schedule


def schedule_article_tweets(article_path: Path, days: int = 7):
    """
    Generate and schedule tweets from an article.

    Args:
        article_path: Path to article index.md
        days: Number of days to spread tweets
    """
    print("=" * 70)
    print("GENERATING TWEET SCHEDULE")
    print("=" * 70)
    print()

    # Parse article
    parser = ArticleParser()
    article = parser.parse_article(article_path)

    print(f"📰 Article: {article.title}")
    print(f"📅 Published: {article.date}")
    print(f"🔗 URL: {article.url}")
    print(f"📚 Stories: {len(article.stories)}")
    print()

    # Compose tweets
    print("✍️  Composing tweets...")
    composer = TweetComposer(article.url)
    tweets = composer.compose_all_tweets(article, include_intro_tweet=False)
    print(f"✓ Composed {len(tweets)} tweets")
    print()

    # Generate schedule
    print(f"📅 Generating {days}-day schedule...")
    schedule = generate_schedule(len(tweets), days=days)
    print(f"✓ Created schedule:")
    print(f"   First: {schedule[0].strftime('%a, %b %d at %I:%M %p')}")
    print(f"   Last:  {schedule[-1].strftime('%a, %b %d at %I:%M %p')}")
    print()

    # Add to queue
    print("💾 Adding tweets to queue...")
    queue = TweetQueue()

    for i, (tweet, post_time) in enumerate(zip(tweets, schedule)):
        story_section = article.stories[i].section if i < len(article.stories) else None

        queue.add_tweet(
            text=tweet['text'],
            scheduled_time=post_time,
            image_path=tweet['image_path'],
            story_section=story_section
        )

    print(f"✓ Queued {len(tweets)} tweets")
    print()

    # Summary
    stats = queue.get_stats()
    print("=" * 70)
    print("SCHEDULE SUMMARY")
    print("=" * 70)
    print(f"Total queued: {stats['total']}")
    print(f"Pending: {stats['pending']}")
    next_time = datetime.fromisoformat(stats['next_scheduled'])
    print(f"Next post: {next_time.strftime('%a, %b %d at %I:%M %p')}")
    print()

    # Preview first 5
    print("📋 First 5 tweets:")
    for i in range(min(5, len(tweets))):
        tweet = tweets[i]
        post_time = schedule[i]
        story = article.stories[i] if i < len(article.stories) else None
        section = f"[{story.section}]" if story else ""

        print(f"  {i+1}. {post_time.strftime('%a %I:%M %p')} {section}")
        print(f"     {tweet['text'][:60]}...")
        print()

    if len(tweets) > 5:
        print(f"  ... and {len(tweets) - 5} more")

    print("=" * 70)


def main():
    if len(sys.argv) < 2:
        print("Usage: python schedule_article.py <article_path> [--days N]")
        sys.exit(1)

    article_path = Path(sys.argv[1])
    days = 7

    # Parse --days argument
    if '--days' in sys.argv:
        idx = sys.argv.index('--days')
        if idx + 1 < len(sys.argv):
            days = int(sys.argv[idx + 1])

    if not article_path.exists():
        print(f"❌ Article not found: {article_path}")
        sys.exit(1)

    schedule_article_tweets(article_path, days)


if __name__ == '__main__':
    main()
