#!/bin/bash
#
# Wrapper script for cron job
# Activates virtual environment and runs the Twitter bot posting script
#

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to project directory
cd "$SCRIPT_DIR"

# Activate virtual environment
source venv/bin/activate

# Run the Twitter bot posting script
python scripts/post_scheduled_tweets.py
