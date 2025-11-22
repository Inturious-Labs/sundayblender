#!/bin/bash

# Podcast Processing Script for Sunday Blender
# Usage: Run this script from a newsletter directory containing index.md and the m4a audio file
# Example: cd content/posts/2025/01/0126 && bash ../../../../scripts/process_podcast.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the current working directory (should be the post directory)
POST_DIR="$(pwd)"

echo -e "${BLUE}🎙️  Sunday Blender Podcast Processor${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check if index.md exists
if [ ! -f "index.md" ]; then
    echo -e "${RED}❌ Error: index.md not found in current directory${NC}"
    echo -e "${YELLOW}💡 Please run this script from a newsletter directory${NC}"
    exit 1
fi

# Extract date from frontmatter
DATE=$(grep -m 1 "^date:" index.md | sed 's/date: *//' | tr -d ' ')
if [ -z "$DATE" ]; then
    echo -e "${RED}❌ Error: Could not find date in frontmatter${NC}"
    exit 1
fi

echo -e "${GREEN}📅 Found date: $DATE${NC}"

# Find m4a file
M4A_FILE=$(find . -maxdepth 1 -name "*.m4a" -type f | head -1)

if [ -z "$M4A_FILE" ]; then
    echo -e "${RED}❌ Error: No .m4a file found in current directory${NC}"
    echo -e "${YELLOW}💡 Please add the NotebookLM audio file (.m4a) to this directory${NC}"
    exit 1
fi

echo -e "${GREEN}🎵 Found audio file: $M4A_FILE${NC}"

# Output filename
OUTPUT_FILE="${DATE}-podcast.mp3"

# Check if ffmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${RED}❌ Error: ffmpeg is not installed${NC}"
    echo -e "${YELLOW}💡 Install with: brew install ffmpeg${NC}"
    exit 1
fi

# Convert m4a to mp3
echo -e "${BLUE}🔄 Converting to MP3...${NC}"
ffmpeg -i "$M4A_FILE" -codec:a libmp3lame -qscale:a 2 "$OUTPUT_FILE" -y 2>&1 | grep -v "^frame=" || true

if [ ! -f "$OUTPUT_FILE" ]; then
    echo -e "${RED}❌ Error: Conversion failed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Converted to: $OUTPUT_FILE${NC}"

# Get file size in bytes
FILESIZE=$(stat -f%z "$OUTPUT_FILE" 2>/dev/null || stat -c%s "$OUTPUT_FILE" 2>/dev/null)
echo -e "${GREEN}📦 File size: $FILESIZE bytes ($(numfmt --to=iec-i --suffix=B $FILESIZE 2>/dev/null || echo "$((FILESIZE / 1024 / 1024)) MB"))${NC}"

# Get duration in seconds using ffprobe
if command -v ffprobe &> /dev/null; then
    DURATION=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$OUTPUT_FILE" | cut -d. -f1)
    DURATION_MIN=$((DURATION / 60))
    DURATION_SEC=$((DURATION % 60))
    echo -e "${GREEN}⏱️  Duration: ${DURATION}s (${DURATION_MIN}m ${DURATION_SEC}s)${NC}"
else
    echo -e "${YELLOW}⚠️  ffprobe not found, cannot determine duration${NC}"
    echo -e "${YELLOW}💡 Install with: brew install ffmpeg (includes ffprobe)${NC}"
    DURATION="0"
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✨ Podcast processing complete!${NC}"
echo ""
echo -e "${YELLOW}📝 Add the following to your frontmatter:${NC}"
echo ""
echo "podcast:"
echo "  enabled: true"
echo "  file: \"$OUTPUT_FILE\""
echo "  duration: $DURATION"
echo "  filesize: $FILESIZE"
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}💡 Next steps:${NC}"
echo -e "  1. Update frontmatter with the podcast section above"
echo -e "  2. Run: ${BLUE}bash ../../../../scripts/generate_transcript.sh${NC}"
echo -e "  3. Test audio playback on your local Hugo server"
echo ""
