# Twitter Bot for The Sunday Blender

Automated tweet scheduling system that posts stories to [@SundayBlender](https://x.com/SundayBlender) over 7 days.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Setup](#setup)
- [Usage](#usage)
- [Dalaran Server Setup](#dalaran-server-setup)
- [Troubleshooting](#troubleshooting)

---

## Overview

This bot automatically:

1. Parses stories from your Sunday Blender articles
2. Generates tweets with smart truncation (280 char limit)
3. Schedules tweets over 7 days at optimal times (8 AM, 12 PM, 6 PM UTC+8)
4. Posts tweets automatically via cron job
5. Tracks posting progress

## Features

- ✅ **Interactive Menu** - View queue status, create schedules, pause/resume
- ✅ **Smart Truncation** - Automatically fits stories to 280 characters
- ✅ **Image Support** - Attaches story images to tweets
- ✅ **Flexible Scheduling** - Spread tweets over customizable days
- ✅ **Pause/Resume** - Stop and restart posting without losing progress
- ✅ **Progress Tracking** - See what's posted, what's pending
- ✅ **Error Handling** - Robust retry logic and logging

---

## Setup

### 1. Twitter Developer Account (Already Done ✅)

You've already set up:
- Twitter Developer account with @SundayBlender
- API credentials stored in `.env`

### 2. Install Dependencies

```bash
pip3 install tweepy python-dotenv pyyaml
```

### 3. Verify Setup

Test your Twitter connection:

```bash
python3 scripts/test_twitter_connection.py
```

You should see: ✅ SUCCESS! Connected to Twitter API

---

## Usage

### Interactive Menu

On `Dalaran`, run the interactive scheduler:

```bash
./scripts/schedule_tweets.sh
```

This will:
1. **Show current queue status**
   - Total tweets, posted, pending
   - Progress bar
   - Next scheduled tweet
   - List of upcoming tweets

2. **Show menu options:**
   - `1)` Create NEW tweet schedule
   - `2)` PAUSE current schedule
   - `3)` RESUME current schedule
   - `4)` CLEAR all tweets from queue
   - `5)` Exit

### Creating a New Schedule

1. Run `./scripts/schedule_tweets.sh`
2. Select option `1` (Create NEW schedule)
3. Choose from the last 3 articles
4. Enter number of days (default: 7)
5. Tweets are queued and ready!

### Pausing/Resuming

**To Pause:**

```bash
./scripts/schedule_tweets.sh
# Select option 2
```

**To Resume:**

```bash
./scripts/schedule_tweets.sh
# Select option 3
```

### Checking Queue Status

```bash
python3 scripts/lib/check_queue_status.py
```

Shows:
- Active/Paused status
- Progress bar
- Next scheduled tweet
- Upcoming 5 tweets
- Recently posted 3 tweets with links

---

### Monitor the Log

```bash
tail -f logs/twitter_bot.log
```

---

## Workflow

### Weekly Publishing Workflow

1. **Publish new article** to your Sunday Blender website

2. **Run scheduler on `Dalaran`:**

   ```bash
   ./scripts/schedule_tweets.sh
   ```

3. **Select the new article** from the menu

4. **Tweets are queued** and will post automatically via cron

5. **Monitor progress:**

   ```bash
   python3 scripts/lib/check_queue_status.py
   ```

### Posting Schedule

Tweets post at optimal times for English-speaking Asian families (UTC+8):

- **8:00 AM** - Morning commute/breakfast
- **12:00 PM** - Lunch break
- **6:00 PM** - Evening commute/dinner

For 18 stories over 7 days:

- Days 1-6: 3 tweets/day (8 AM, 12 PM, 6 PM)
- Day 7: 2 tweets/day (8 AM, 12 PM)

---

## File Structure

```
sundayblender/
├── scripts/
│   ├── schedule_tweets.sh          # Interactive menu (run this!)
│   ├── post_scheduled_tweets.py    # Cron job script
│   ├── test_twitter_connection.py  # Test Twitter API
│   ├── post_test_tweet.py          # Manual tweet posting
│   └── lib/
│       ├── article_parser.py       # Extract stories from articles
│       ├── tweet_composer.py       # Format tweets
│       ├── tweet_queue.py          # Queue management
│       ├── twitter_client.py       # Twitter API wrapper
│       ├── check_queue_status.py   # View queue status
│       ├── manage_queue.py         # Pause/resume/clear
│       └── schedule_article.py     # Generate schedules
├── data/
│   ├── tweet_queue.json           # Queue storage
│   └── .queue_paused              # Pause flag (if exists)
├── logs/
│   └── twitter_bot.log            # Cron job logs
└── .env                            # Twitter API credentials (SECRET!)
```

---

## Troubleshooting

All actions shall be performed on `Dalaran`.

### Tweets Not Posting

1. **Check if paused:**

   ```bash
   python3 scripts/lib/manage_queue.py --status
   ```

2. **Check cron is running:**

   ```bash
   crontab -l
   ```

3. **Check logs:**

   ```bash
   tail -50 logs/twitter_bot.log
   ```

4. **Manual test:**

   ```bash
   python3 scripts/post_scheduled_tweets.py
   ```

### Authentication Errors

1. **Verify credentials:**

   ```bash
   python3 scripts/test_twitter_connection.py
   ```

2. **Check `.env` file exists and has correct values**

3. **Regenerate tokens** in Twitter Developer Portal if needed

### Queue Issues

**Clear and restart:**

```bash
./scripts/schedule_tweets.sh
# Select option 4 (Clear queue)
# Then create a new schedule
```

### Tweet Too Long

The composer automatically truncates tweets to `280` chars. If you see issues:

- Story content is truncated smartly at sentence boundaries
- Link is always included
- Hashtags removed if needed to fit

---

### Queue Data Location

- **Queue file:** `data/tweet_queue.json`
- **Pause flag:** `data/.queue_paused`
- **Logs:** `logs/twitter_bot.log`

---

## Future Enhancements

Potential improvements:

- Hashtag strategy optimization
- Analytics tracking (UTM parameters)
- Tweet performance metrics
- A/B testing different posting times
- Automated image optimization
- Thread support for long stories

---
