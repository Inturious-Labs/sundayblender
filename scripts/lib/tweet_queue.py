"""
Tweet Queue Manager for The Sunday Blender
Manages scheduled tweets stored in JSON format.
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class QueuedTweet:
    """Represents a scheduled tweet in the queue."""
    id: str  # Unique ID (timestamp-based)
    text: str
    image_path: Optional[str]
    scheduled_time: str  # ISO format timestamp
    posted: bool = False
    posted_time: Optional[str] = None
    tweet_id: Optional[str] = None  # Twitter tweet ID after posting
    story_section: Optional[str] = None  # For reference


class TweetQueue:
    """Manages the tweet queue stored in JSON."""

    def __init__(self, queue_file: Path = None):
        """
        Initialize tweet queue.

        Args:
            queue_file: Path to JSON file (defaults to data/tweet_queue.json)
        """
        if queue_file is None:
            queue_file = Path(__file__).parent.parent.parent / 'data' / 'tweet_queue.json'

        self.queue_file = queue_file
        self.queue_file.parent.mkdir(parents=True, exist_ok=True)

        # Load existing queue or create new
        self.tweets = self._load_queue()

    def _load_queue(self) -> List[QueuedTweet]:
        """Load queue from JSON file."""
        if not self.queue_file.exists():
            return []

        try:
            with open(self.queue_file, 'r') as f:
                data = json.load(f)
                return [QueuedTweet(**tweet) for tweet in data]
        except (json.JSONDecodeError, TypeError) as e:
            print(f"⚠ Warning: Could not load queue file: {e}")
            return []

    def _save_queue(self):
        """Save queue to JSON file."""
        data = [asdict(tweet) for tweet in self.tweets]
        with open(self.queue_file, 'w') as f:
            json.dump(data, f, indent=2)

    def add_tweet(
        self,
        text: str,
        scheduled_time: datetime,
        image_path: Optional[str] = None,
        story_section: Optional[str] = None
    ) -> QueuedTweet:
        """
        Add a tweet to the queue.

        Args:
            text: Tweet text
            scheduled_time: When to post the tweet
            image_path: Optional path to image
            story_section: Optional section name for reference

        Returns:
            QueuedTweet object
        """
        # Generate unique ID
        tweet_id = scheduled_time.strftime('%Y%m%d%H%M%S')

        tweet = QueuedTweet(
            id=tweet_id,
            text=text,
            image_path=image_path,
            scheduled_time=scheduled_time.isoformat(),
            story_section=story_section
        )

        self.tweets.append(tweet)
        self._save_queue()

        return tweet

    def get_due_tweets(self, now: datetime = None) -> List[QueuedTweet]:
        """
        Get tweets that are due to be posted.

        Args:
            now: Current time (defaults to datetime.now())

        Returns:
            List of tweets scheduled for now or earlier that haven't been posted
        """
        if now is None:
            now = datetime.now()

        due_tweets = []
        for tweet in self.tweets:
            if tweet.posted:
                continue

            scheduled = datetime.fromisoformat(tweet.scheduled_time)
            if scheduled <= now:
                due_tweets.append(tweet)

        return due_tweets

    def mark_posted(self, tweet_id: str, twitter_tweet_id: str):
        """
        Mark a tweet as posted.

        Args:
            tweet_id: Queue tweet ID
            twitter_tweet_id: Twitter's tweet ID
        """
        for tweet in self.tweets:
            if tweet.id == tweet_id:
                tweet.posted = True
                tweet.posted_time = datetime.now().isoformat()
                tweet.tweet_id = twitter_tweet_id
                break

        self._save_queue()

    def get_pending_count(self) -> int:
        """Get count of unposted tweets."""
        return sum(1 for tweet in self.tweets if not tweet.posted)

    def get_next_scheduled(self) -> Optional[QueuedTweet]:
        """Get the next scheduled tweet."""
        pending = [t for t in self.tweets if not t.posted]
        if not pending:
            return None

        return min(pending, key=lambda t: t.scheduled_time)

    def clear_posted(self):
        """Remove posted tweets from queue (cleanup)."""
        self.tweets = [t for t in self.tweets if not t.posted]
        self._save_queue()

    def get_stats(self) -> Dict:
        """Get queue statistics."""
        total = len(self.tweets)
        posted = sum(1 for t in self.tweets if t.posted)
        pending = total - posted

        next_tweet = self.get_next_scheduled()
        next_time = None
        if next_tweet:
            next_time = datetime.fromisoformat(next_tweet.scheduled_time)

        return {
            'total': total,
            'posted': posted,
            'pending': pending,
            'next_scheduled': next_time.isoformat() if next_time else None
        }


def generate_schedule(
    num_tweets: int,
    start_time: datetime = None,
    days: int = 7,
    posts_per_day: int = 3
) -> List[datetime]:
    """
    Generate evenly distributed posting times over a period.

    Args:
        num_tweets: Number of tweets to schedule
        start_time: When to start (defaults to now)
        days: Number of days to spread tweets over
        posts_per_day: Target posts per day

    Returns:
        List of datetime objects for posting times
    """
    if start_time is None:
        start_time = datetime.now()

    # Optimal posting hours for English-speaking Asian families (UTC+8)
    # 8 AM: Morning commute/breakfast
    # 12 PM: Lunch break
    # 6 PM: Evening commute/dinner time
    posting_hours = [8, 12, 18]

    schedule = []
    tweets_per_day = num_tweets // days
    remainder = num_tweets % days

    current_day = start_time.replace(hour=8, minute=0, second=0, microsecond=0)

    # If start time is after 6 PM, start tomorrow
    if start_time.hour >= 18:
        current_day += timedelta(days=1)

    for day in range(days):
        # Distribute tweets for this day
        day_tweets = tweets_per_day + (1 if day < remainder else 0)

        # Select hours for this day's tweets
        hours = posting_hours[:day_tweets] if day_tweets <= len(posting_hours) else posting_hours

        for i, hour in enumerate(hours[:day_tweets]):
            post_time = current_day.replace(hour=hour)
            schedule.append(post_time)

        current_day += timedelta(days=1)

    return schedule[:num_tweets]  # Ensure exact count


def main():
    """Test the tweet queue."""
    queue = TweetQueue()

    print("Tweet Queue Manager")
    print("=" * 60)

    stats = queue.get_stats()
    print(f"Total tweets: {stats['total']}")
    print(f"Posted: {stats['posted']}")
    print(f"Pending: {stats['pending']}")

    if stats['next_scheduled']:
        next_time = datetime.fromisoformat(stats['next_scheduled'])
        print(f"Next scheduled: {next_time.strftime('%Y-%m-%d %H:%M')}")

    print()

    # Test schedule generation
    print("Generating sample 7-day schedule for 18 tweets:")
    schedule = generate_schedule(18, days=7)

    for i, post_time in enumerate(schedule, 1):
        print(f"  Tweet {i:2d}: {post_time.strftime('%a, %b %d at %I:%M %p')}")


if __name__ == '__main__':
    main()
