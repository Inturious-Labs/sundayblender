#!/usr/bin/env python3
"""
Manage the tweet queue - pause, resume, clear operations.
"""

import sys
import json
from pathlib import Path

# Import modules
try:
    from tweet_queue import TweetQueue
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from tweet_queue import TweetQueue


def pause_queue():
    """Pause the tweet queue by creating a .paused flag file."""
    pause_file = Path(__file__).parent.parent.parent / 'data' / '.queue_paused'
    pause_file.parent.mkdir(parents=True, exist_ok=True)
    pause_file.write_text('paused')

    queue = TweetQueue()
    stats = queue.get_stats()

    print("=" * 70)
    print("⏸️  QUEUE PAUSED")
    print("=" * 70)
    print(f"\n✓ Tweet posting has been paused.")
    print(f"\nQueue status:")
    print(f"  Total tweets: {stats['total']}")
    print(f"  Pending: {stats['pending']}")
    print(f"  Posted: {stats['posted']}")
    print(f"\n💡 The cron job will skip posting while paused.")
    print(f"   To resume, run: ./scripts/schedule_tweets.sh and select 'Resume'")
    print("=" * 70)


def resume_queue():
    """Resume the tweet queue by removing the .paused flag file."""
    pause_file = Path(__file__).parent.parent.parent / 'data' / '.queue_paused'

    if not pause_file.exists():
        print("=" * 70)
        print("ℹ️  Queue is NOT paused")
        print("=" * 70)
        print("\n✓ Tweet posting is already active.")
        print("=" * 70)
        return

    pause_file.unlink()

    queue = TweetQueue()
    stats = queue.get_stats()

    print("=" * 70)
    print("▶️  QUEUE RESUMED")
    print("=" * 70)
    print(f"\n✓ Tweet posting has been resumed.")
    print(f"\nQueue status:")
    print(f"  Total tweets: {stats['total']}")
    print(f"  Pending: {stats['pending']}")
    print(f"  Posted: {stats['posted']}")

    if stats['next_scheduled']:
        from datetime import datetime
        next_time = datetime.fromisoformat(stats['next_scheduled'])
        print(f"\nNext scheduled tweet:")
        print(f"  {next_time.strftime('%A, %B %d at %I:%M %p')}")

    print(f"\n💡 The cron job will now post tweets on schedule.")
    print("=" * 70)


def clear_queue():
    """Clear all tweets from the queue."""
    queue = TweetQueue()
    stats_before = queue.get_stats()

    # Clear the queue
    queue.tweets = []
    queue._save_queue()

    print("=" * 70)
    print("🗑️  QUEUE CLEARED")
    print("=" * 70)
    print(f"\n✓ Removed {stats_before['total']} tweets from the queue.")
    print(f"  - {stats_before['posted']} were already posted")
    print(f"  - {stats_before['pending']} were pending")
    print(f"\n💡 Queue is now empty. Create a new schedule when ready.")
    print("=" * 70)


def is_paused():
    """Check if the queue is paused."""
    pause_file = Path(__file__).parent.parent.parent / 'data' / '.queue_paused'
    return pause_file.exists()


def main():
    """Main CLI for queue management."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python manage_queue.py --pause")
        print("  python manage_queue.py --resume")
        print("  python manage_queue.py --clear")
        print("  python manage_queue.py --status")
        sys.exit(1)

    action = sys.argv[1]

    if action == '--pause':
        pause_queue()
    elif action == '--resume':
        resume_queue()
    elif action == '--clear':
        clear_queue()
    elif action == '--status':
        if is_paused():
            print("⏸️  Queue is PAUSED")
        else:
            print("▶️  Queue is ACTIVE")
    else:
        print(f"Unknown action: {action}")
        sys.exit(1)


if __name__ == '__main__':
    main()
