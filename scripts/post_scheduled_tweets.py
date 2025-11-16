#!/usr/bin/env python3
"""
Post Scheduled Tweets - Cron Job Script

This script checks the tweet queue and posts any tweets that are due.
Run this via cron on your Dalaran server (e.g., every 15 minutes).

Example crontab:
    */15 * * * * cd /path/to/sundayblender && python scripts/post_scheduled_tweets.py >> logs/twitter_bot.log 2>&1
"""

import sys
from pathlib import Path
from datetime import datetime

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent / 'lib'))

from tweet_queue import TweetQueue
from twitter_client import TwitterClient


def is_paused():
    """Check if queue is paused."""
    pause_file = Path(__file__).parent.parent / 'data' / '.queue_paused'
    return pause_file.exists()


def post_due_tweets():
    """Check queue and post any tweets that are due."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    print(f"\n{'=' * 70}")
    print(f"Twitter Bot - Scheduled Tweet Posting")
    print(f"Run time: {timestamp}")
    print(f"{'=' * 70}")

    # Check if paused
    if is_paused():
        print("\n⏸️  Queue is PAUSED - skipping tweet posting")
        print("   (Run ./scripts/schedule_tweets.sh and select 'Resume' to restart)")
        print(f"{'=' * 70}\n")
        return

    # Load queue
    queue = TweetQueue()

    # Get due tweets
    due_tweets = queue.get_due_tweets()

    if not due_tweets:
        stats = queue.get_stats()
        print(f"\n✓ No tweets due at this time")
        print(f"  Pending: {stats['pending']}")

        if stats['next_scheduled']:
            next_time = datetime.fromisoformat(stats['next_scheduled'])
            print(f"  Next: {next_time.strftime('%a, %b %d at %I:%M %p')}")

        print(f"{'=' * 70}\n")
        return

    print(f"\n📬 Found {len(due_tweets)} tweet(s) ready to post\n")

    # Initialize Twitter client
    try:
        client = TwitterClient()
    except Exception as e:
        print(f"❌ Failed to initialize Twitter client: {e}")
        print(f"{'=' * 70}\n")
        return

    # Post each due tweet
    posted_count = 0
    failed_count = 0

    for i, tweet in enumerate(due_tweets, 1):
        scheduled_time = datetime.fromisoformat(tweet.scheduled_time)

        print(f"Posting tweet {i}/{len(due_tweets)}...")
        print(f"  Scheduled: {scheduled_time.strftime('%a, %b %d at %I:%M %p')}")
        if tweet.story_section:
            print(f"  Section: [{tweet.story_section}]")
        print(f"  Text: {tweet.text[:60]}...")

        try:
            # Post the tweet
            response = client.post_tweet(tweet.text, tweet.image_path)

            # Mark as posted
            queue.mark_posted(tweet.id, response['id'])

            posted_count += 1
            print(f"  ✅ Posted successfully!")
            print(f"  🔗 {response['url']}")

        except Exception as e:
            failed_count += 1
            print(f"  ❌ Failed to post: {e}")

        print()

    # Summary
    print(f"{'=' * 70}")
    print(f"Summary:")
    print(f"  ✅ Posted: {posted_count}")
    if failed_count > 0:
        print(f"  ❌ Failed: {failed_count}")

    stats = queue.get_stats()
    print(f"\nQueue status:")
    print(f"  Total: {stats['total']}")
    print(f"  Pending: {stats['pending']}")
    print(f"  Posted: {stats['posted']}")

    if stats['next_scheduled']:
        next_time = datetime.fromisoformat(stats['next_scheduled'])
        print(f"\nNext scheduled: {next_time.strftime('%a, %b %d at %I:%M %p')}")

    print(f"{'=' * 70}\n")


def main():
    """Main entry point."""
    try:
        post_due_tweets()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
