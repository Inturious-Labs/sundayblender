#!/usr/bin/env python3
"""
Check and display the current tweet queue status.
"""

import sys
from pathlib import Path
from datetime import datetime

# Import modules
try:
    from tweet_queue import TweetQueue
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from tweet_queue import TweetQueue


def is_paused():
    """Check if queue is paused."""
    pause_file = Path(__file__).parent.parent.parent / 'data' / '.queue_paused'
    return pause_file.exists()


def display_queue_status():
    """Display comprehensive queue status."""
    queue = TweetQueue()

    stats = queue.get_stats()
    paused = is_paused()

    # Header
    print("=" * 70)
    print("CURRENT TWEET QUEUE STATUS")
    print("=" * 70)

    # Show pause status
    if paused:
        print("\n⏸️  STATUS: PAUSED - Tweets will NOT be posted")
        print("   (Resume from the menu to start posting again)")
    else:
        print("\n▶️  STATUS: ACTIVE - Tweets will be posted on schedule")

    # Check if queue is empty
    if stats['total'] == 0:
        print("\n📭 Queue is EMPTY - No tweets scheduled")
        print("\nℹ️  You can create a new schedule by selecting 'y' below.")
        print("=" * 70)
        return

    # Basic stats
    print(f"\n📊 Queue Statistics:")
    print(f"   Total tweets: {stats['total']}")
    print(f"   ✅ Posted: {stats['posted']}")
    print(f"   ⏳ Pending: {stats['pending']}")

    # Progress bar
    if stats['total'] > 0:
        progress = stats['posted'] / stats['total']
        bar_length = 40
        filled = int(bar_length * progress)
        bar = '█' * filled + '░' * (bar_length - filled)
        percentage = progress * 100
        print(f"\n   Progress: [{bar}] {percentage:.1f}%")

    # Next scheduled tweet
    if stats['next_scheduled']:
        next_time = datetime.fromisoformat(stats['next_scheduled'])
        now = datetime.now()
        time_until = next_time - now

        print(f"\n📅 Next Scheduled Tweet:")
        print(f"   Time: {next_time.strftime('%A, %B %d at %I:%M %p')}")

        if time_until.total_seconds() > 0:
            days = time_until.days
            hours = time_until.seconds // 3600
            minutes = (time_until.seconds % 3600) // 60

            time_str = []
            if days > 0:
                time_str.append(f"{days} day{'s' if days > 1 else ''}")
            if hours > 0:
                time_str.append(f"{hours} hour{'s' if hours > 1 else ''}")
            if minutes > 0:
                time_str.append(f"{minutes} minute{'s' if minutes > 1 else ''}")

            print(f"   In: {', '.join(time_str)}")
        else:
            print(f"   Status: ⚠️  OVERDUE (should have posted already!)")

    # Show upcoming tweets
    pending_tweets = [t for t in queue.tweets if not t.posted]

    if pending_tweets:
        print(f"\n📋 Upcoming Tweets (next 5):")

        for i, tweet in enumerate(pending_tweets[:5], 1):
            scheduled = datetime.fromisoformat(tweet.scheduled_time)
            section = f"[{tweet.story_section}]" if tweet.story_section else ""

            print(f"\n   {i}. {scheduled.strftime('%a, %b %d at %I:%M %p')} {section}")
            print(f"      {tweet.text[:55]}...")

        if len(pending_tweets) > 5:
            print(f"\n   ... and {len(pending_tweets) - 5} more pending tweets")

    # Show recently posted
    posted_tweets = [t for t in queue.tweets if t.posted]

    if posted_tweets:
        print(f"\n✅ Recently Posted (last 3):")

        # Sort by posted time, most recent first
        posted_tweets.sort(key=lambda t: t.posted_time or '', reverse=True)

        for i, tweet in enumerate(posted_tweets[:3], 1):
            posted_time = datetime.fromisoformat(tweet.posted_time) if tweet.posted_time else None
            section = f"[{tweet.story_section}]" if tweet.story_section else ""

            if posted_time:
                print(f"\n   {i}. {posted_time.strftime('%a, %b %d at %I:%M %p')} {section}")
            else:
                print(f"\n   {i}. (unknown time) {section}")

            print(f"      {tweet.text[:55]}...")

            if tweet.tweet_id:
                print(f"      🔗 https://twitter.com/SundayBlender/status/{tweet.tweet_id}")

    print("\n" + "=" * 70)


def main():
    display_queue_status()


if __name__ == '__main__':
    main()
