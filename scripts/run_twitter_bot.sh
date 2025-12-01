#!/bin/bash
#
# Wrapper script for cron job
# Activates virtual environment and runs the Twitter bot posting script
#
# Uses flock to prevent multiple concurrent runs (prevents zombie process pile-up)
#

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to project root directory (parent of scripts/)
cd "$SCRIPT_DIR/.."

# Lock file to prevent concurrent runs
LOCKFILE="/tmp/sundayblender_twitter_bot.lock"

# Use flock to ensure only one instance runs at a time
# -n: non-blocking (exit immediately if lock can't be acquired)
# -E 0: exit with code 0 if lock fails (so cron doesn't report error)
exec 200>"$LOCKFILE"
if ! flock -n 200; then
    echo "$(date): Another instance is already running, skipping..."
    exit 0
fi

# Activate virtual environment
source venv/bin/activate

# Run the Twitter bot posting script
python3 scripts/post_scheduled_tweets.py

# Lock is automatically released when script exits
