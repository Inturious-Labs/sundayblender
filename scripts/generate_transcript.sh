#!/bin/bash

# Transcript Generation Script for Sunday Blender Podcast
# Usage: Run this script from a newsletter directory containing index.md
# Example: cd content/posts/2025/01/0126 && bash ../../../../scripts/generate_transcript.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}📝 Sunday Blender Transcript Generator${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check if index.md exists
if [ ! -f "index.md" ]; then
    echo -e "${RED}❌ Error: index.md not found in current directory${NC}"
    echo -e "${YELLOW}💡 Please run this script from a newsletter directory${NC}"
    exit 1
fi

# Extract title and date from frontmatter
TITLE=$(grep -m 1 "^title:" index.md | sed 's/title: *//' | tr -d '"' | tr -d "'")
DATE=$(grep -m 1 "^date:" index.md | sed 's/date: *//' | tr -d ' ')

if [ -z "$TITLE" ] || [ -z "$DATE" ]; then
    echo -e "${RED}❌ Error: Could not find title or date in frontmatter${NC}"
    exit 1
fi

# Format date for display
FORMATTED_DATE=$(date -j -f "%Y-%m-%d" "$DATE" "+%B %d, %Y" 2>/dev/null || date -d "$DATE" "+%B %d, %Y" 2>/dev/null)

echo -e "${GREEN}📄 Title: $TITLE${NC}"
echo -e "${GREEN}📅 Date: $FORMATTED_DATE${NC}"
echo ""

# Output filename
OUTPUT_FILE="transcript.txt"

echo -e "${BLUE}🔄 Generating transcript...${NC}"

# Create transcript header
cat > "$OUTPUT_FILE" << EOF
THE SUNDAY BLENDER PODCAST TRANSCRIPT
═════════════════════════════════════

Title: $TITLE
Date: $FORMATTED_DATE
URL: https://weekly.sundayblender.com/

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EOF

# Extract content from markdown, removing:
# - Frontmatter (between --- and ---)
# - Markdown headers (## becomes just the text)
# - Markdown formatting (**, *, `, etc.)
# - HTML comments
# - Images ![...](...)
# - Links [text](url) becomes just text
# - Code blocks

awk '
BEGIN { in_frontmatter=0; in_code_block=0; }

# Skip frontmatter
/^---$/ {
    if (NR == 1) {
        in_frontmatter=1;
        next;
    } else if (in_frontmatter) {
        in_frontmatter=0;
        next;
    }
}

in_frontmatter { next; }

# Handle code blocks
/^```/ {
    in_code_block = !in_code_block;
    next;
}

in_code_block { next; }

# Skip empty lines at start
NF == 0 && !printed { next; }

# Skip image references
/^!\[.*\]\(.*\)$/ { next; }

# Skip horizontal rules
/^---+$/ { next; }
/^━━━+$/ { next; }

# Process content
{
    printed=1;
    line = $0;

    # Remove HTML comments
    gsub(/<!--.*-->/, "", line);

    # Convert headers to uppercase plain text
    if (match(line, /^#+\s+(.*)/, arr)) {
        line = toupper(arr[1]);
        print "";
        print line;
        print "";
        next;
    }

    # Remove inline images
    gsub(/!\[[^\]]*\]\([^\)]*\)/, "", line);

    # Convert links [text](url) to just text
    while (match(line, /\[([^\]]+)\]\([^\)]+\)/, arr)) {
        gsub(/\[[^\]]+\]\([^\)]+\)/, arr[1], line);
    }

    # Remove bold
    gsub(/\*\*([^*]+)\*\*/, "\\1", line);

    # Remove italic
    gsub(/\*([^*]+)\*/, "\\1", line);

    # Remove code ticks
    gsub(/`([^`]+)`/, "\\1", line);

    # Clean up extra spaces
    gsub(/  +/, " ", line);
    gsub(/^ /, "", line);
    gsub(/ $/, "", line);

    # Print if not empty
    if (length(line) > 0) {
        print line;
    }
}
' index.md >> "$OUTPUT_FILE"

# Add footer
cat >> "$OUTPUT_FILE" << EOF

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

© 2025 Inturious Labs
Visit us at: https://weekly.sundayblender.com
Powered by Internet Computer

For questions or feedback, contact: clayton.man@sundayblender.com

EOF

# Count words and lines
WORD_COUNT=$(wc -w < "$OUTPUT_FILE" | tr -d ' ')
LINE_COUNT=$(wc -l < "$OUTPUT_FILE" | tr -d ' ')

echo -e "${GREEN}✅ Transcript generated: $OUTPUT_FILE${NC}"
echo -e "${GREEN}📊 Statistics: $LINE_COUNT lines, $WORD_COUNT words${NC}"
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✨ Transcript ready for distribution!${NC}"
echo ""
echo -e "${YELLOW}💡 Use cases:${NC}"
echo -e "  • Copy to podcast platforms (Apple Podcasts, Spotify)"
echo -e "  • Submit for accessibility compliance"
echo -e "  • Share as plain text version"
echo -e "  • Use for SEO optimization"
echo ""
