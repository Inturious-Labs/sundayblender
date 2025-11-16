"""
Twitter Client for The Sunday Blender
Handles authentication, posting tweets with images, and error handling.
"""

import os
import tweepy
from pathlib import Path
from typing import Optional, List
from dotenv import load_dotenv


class TwitterClient:
    """Wrapper for Twitter API operations."""

    def __init__(self, env_path: Optional[Path] = None):
        """
        Initialize Twitter client.

        Args:
            env_path: Path to .env file (defaults to project root)
        """
        # Load environment variables
        if env_path is None:
            env_path = Path(__file__).parent.parent.parent / '.env'

        if not env_path.exists():
            raise FileNotFoundError(f".env file not found at {env_path}")

        load_dotenv(env_path)

        # Get credentials
        api_key = os.getenv('TWITTER_API_KEY')
        api_secret = os.getenv('TWITTER_API_SECRET')
        access_token = os.getenv('TWITTER_ACCESS_TOKEN')
        access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET')

        if not all([api_key, api_secret, access_token, access_token_secret]):
            raise ValueError("Missing Twitter API credentials in .env file")

        # Authenticate
        auth = tweepy.OAuthHandler(api_key, api_secret)
        auth.set_access_token(access_token, access_token_secret)

        # Create API client (v1.1 for media upload)
        self.api = tweepy.API(auth, wait_on_rate_limit=True)

        # Create client for API v2 (for posting)
        self.client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
            wait_on_rate_limit=True
        )

        # Verify credentials
        try:
            user = self.api.verify_credentials()
            self.username = user.screen_name
            print(f"✓ Authenticated as @{self.username}")
        except tweepy.TweepyException as e:
            raise Exception(f"Authentication failed: {e}")

    def post_tweet(
        self,
        text: str,
        image_path: Optional[str] = None,
        reply_to_id: Optional[str] = None
    ) -> dict:
        """
        Post a tweet with optional image.

        Args:
            text: Tweet text (max 280 characters)
            image_path: Optional path to image file
            reply_to_id: Optional tweet ID to reply to

        Returns:
            Tweet response dict with 'id' and 'text'

        Raises:
            tweepy.TweepyException: If posting fails
        """
        # Validate text length
        if len(text) > 280:
            raise ValueError(f"Tweet text too long: {len(text)} characters (max 280)")

        media_ids = []

        # Upload image if provided
        if image_path:
            image_path = Path(image_path)
            if not image_path.exists():
                print(f"⚠ Warning: Image not found at {image_path}, posting without image")
            else:
                try:
                    media = self.api.media_upload(filename=str(image_path))
                    media_ids = [media.media_id]
                    print(f"✓ Uploaded image: {image_path.name}")
                except tweepy.TweepyException as e:
                    print(f"⚠ Warning: Image upload failed: {e}, posting without image")

        # Post tweet
        try:
            response = self.client.create_tweet(
                text=text,
                media_ids=media_ids if media_ids else None,
                in_reply_to_tweet_id=reply_to_id
            )

            tweet_id = response.data['id']
            print(f"✅ Tweet posted: {tweet_id}")
            print(f"   URL: https://twitter.com/{self.username}/status/{tweet_id}")

            return {
                'id': tweet_id,
                'text': text,
                'url': f"https://twitter.com/{self.username}/status/{tweet_id}"
            }

        except tweepy.TweepyException as e:
            print(f"❌ Failed to post tweet: {e}")
            raise

    def post_thread(self, tweets: List[dict]) -> List[dict]:
        """
        Post a thread of tweets.

        Args:
            tweets: List of dicts with 'text' and optional 'image_path'

        Returns:
            List of tweet response dicts

        Example:
            tweets = [
                {'text': 'First tweet', 'image_path': '/path/to/image.jpg'},
                {'text': 'Second tweet'},
                {'text': 'Third tweet'}
            ]
        """
        responses = []
        reply_to_id = None

        for i, tweet_data in enumerate(tweets, 1):
            print(f"\nPosting tweet {i}/{len(tweets)}...")

            response = self.post_tweet(
                text=tweet_data['text'],
                image_path=tweet_data.get('image_path'),
                reply_to_id=reply_to_id
            )

            responses.append(response)
            reply_to_id = response['id']  # Next tweet replies to this one

        print(f"\n✅ Thread posted: {len(responses)} tweets")
        return responses

    def get_rate_limit_status(self) -> dict:
        """Get current API rate limit status."""
        try:
            status = self.api.rate_limit_status()
            return status
        except tweepy.TweepyException as e:
            print(f"Failed to get rate limit status: {e}")
            return {}


def main():
    """Test the Twitter client."""
    import sys

    client = TwitterClient()

    if len(sys.argv) > 1:
        # Post a test tweet
        text = sys.argv[1]
        image = sys.argv[2] if len(sys.argv) > 2 else None

        print(f"\nPosting test tweet:")
        print(f"  Text: {text}")
        if image:
            print(f"  Image: {image}")

        response = client.post_tweet(text, image)
        print(f"\n✅ Success! Tweet ID: {response['id']}")

    else:
        print(f"✓ Twitter client initialized successfully")
        print(f"  Username: @{client.username}")
        print("\nUsage:")
        print(f"  python {__file__} 'Tweet text' [image_path]")


if __name__ == '__main__':
    main()
