#!/bin/bash
#
# Interactive Tweet Scheduler for The Sunday Blender
# Shows recent articles and generates tweet schedule for selected article
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

echo "========================================"
echo " Sunday Blender Tweet Scheduler"
echo "========================================"
echo

# Check current queue status
echo "📊 Checking current tweet queue status..."
echo

python scripts/lib/check_queue_status.py

echo
echo "----------------------------------------"
echo

# Show menu options
echo
echo "What would you like to do?"
echo
echo "  1) Create a NEW tweet schedule (replaces existing queue)"
echo "  2) PAUSE current schedule (stops posting tweets)"
echo "  3) RESUME current schedule (restarts posting)"
echo "  4) CLEAR all tweets from queue"
echo "  5) Exit (no changes)"
echo

read -p "Enter your choice (1-5): " menu_choice

case $menu_choice in
    1)
        echo
        echo "⚠️  Warning: Creating a new schedule will REPLACE the existing queue!"
        read -p "Are you sure? (y/n): " confirm

        if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
            echo "Cancelled."
            exit 0
        fi
        # Continue to create new schedule
        ;;
    2)
        echo
        echo "⏸️  PAUSING tweet schedule..."
        python scripts/lib/manage_queue.py --pause
        exit 0
        ;;
    3)
        echo
        echo "▶️  RESUMING tweet schedule..."
        python scripts/lib/manage_queue.py --resume
        exit 0
        ;;
    4)
        echo
        echo "⚠️  Warning: This will DELETE all tweets from the queue!"
        read -p "Are you sure? (y/n): " confirm

        if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
            echo "Cancelled."
            exit 0
        fi

        echo
        echo "🗑️  Clearing queue..."
        python scripts/lib/manage_queue.py --clear
        exit 0
        ;;
    5)
        echo "Exiting. No changes made."
        exit 0
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac

# Find recent articles
echo
echo "📚 Finding recent articles..."
ARTICLES=($(find content/posts/2025 -name "index.md" -type f | sort -r | head -3))

if [ ${#ARTICLES[@]} -eq 0 ]; then
    echo "❌ No articles found!"
    exit 1
fi

echo
echo "Select an article to schedule tweets:"
echo

# Display articles with metadata
for i in "${!ARTICLES[@]}"; do
    article="${ARTICLES[$i]}"

    # Extract title and date from frontmatter
    title=$(grep "^title:" "$article" | sed 's/title: *"\(.*\)"/\1/' | sed "s/title: *'\(.*\)'/\1/" | sed 's/title: *//')
    date=$(grep "^date:" "$article" | sed 's/date: *//')

    num=$((i + 1))
    echo "  $num) $date - $title"
    echo "     Path: $article"
    echo
done

# Get user selection
while true; do
    read -p "Enter your choice (1-${#ARTICLES[@]}), or 'q' to quit: " choice

    if [ "$choice" = "q" ] || [ "$choice" = "Q" ]; then
        echo "Cancelled."
        exit 0
    fi

    if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le "${#ARTICLES[@]}" ]; then
        break
    fi

    echo "Invalid choice. Please enter a number between 1 and ${#ARTICLES[@]}."
done

# Get selected article
idx=$((choice - 1))
selected_article="${ARTICLES[$idx]}"

echo
echo "✓ Selected: $selected_article"
echo

# Ask for number of days
read -p "How many days to spread tweets? (default: 7): " days
days=${days:-7}

echo
echo "🚀 Generating tweet schedule for $days days..."
echo

# Run the Python script
python scripts/lib/schedule_article.py "$selected_article" --days "$days"

echo
echo "✅ Done! Your tweets are scheduled."
echo
echo "Next steps:"
echo "  1. Review the queue: cat data/tweet_queue.json"
echo "  2. Set up cron job on Dalaran server (see README.md)"
echo
