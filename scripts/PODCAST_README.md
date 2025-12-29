# Sunday Blender Podcast Automation

This guide explains how to use the automated podcast workflow for The Sunday Blender newsletter.

## Overview

The podcast automation consists of two main scripts:

1. **`tsb-podcast`** - Processes NotebookLM audio files (m4a → mp3)
2. **`tsb-transcript`** - Generates plain text transcripts from articles

## Prerequisites

### Required Software

Install ffmpeg for audio processing:
```bash
brew install ffmpeg
```

Verify installation:
```bash
ffmpeg -version
ffprobe -version
```

## Workflow

### Step 1: Generate Audio with NotebookLM

1. Copy the content from your newsletter issue
2. Paste into Google NotebookLM
3. Generate audio discussion
4. Download the `.m4a` file
5. Move the `.m4a` file to your newsletter directory

Example:
```bash
# Your newsletter directory structure
content/posts/2026/20260126/
├── index.md
├── NotebookLM_Audio_20250126.m4a  ← Downloaded audio file
└── [other image files]
```

### Step 2: Process the Audio File

Navigate to your newsletter directory and run:
```bash
cd content/posts/2026/20260126
tsb-podcast
```

This script will:
- ✅ Find the `.m4a` file automatically
- ✅ Convert it to MP3 format (optimized for web)
- ✅ Rename it to `YYYY-MM-DD-podcast.mp3`
- ✅ Calculate duration in seconds
- ✅ Calculate file size in bytes
- ✅ Display frontmatter code to copy

Example output:
```
🎙️  Sunday Blender Podcast Processor
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 Found date: 2025-01-26
🎵 Found audio file: ./NotebookLM_Audio_20250126.m4a
🔄 Converting to MP3...
✅ Converted to: 2025-01-26-podcast.mp3
📦 File size: 10598327 bytes (10.1 MiB)
⏱️  Duration: 662s (11m 2s)

✨ Podcast processing complete!

📝 Add the following to your frontmatter:

podcast:
  enabled: true
  file: "2025-01-26-podcast.mp3"
  duration: 662
  filesize: 10598327
```

### Step 3: Update Frontmatter

Copy the generated frontmatter section and add it to your `index.md`:

```yaml
---
title: "Your Newsletter Title"
date: 2025-01-26
description: "Your description"
tags: ["tag1", "tag2"]
draft: false
slug: "your-slug"
featured_image: "image.jpg"
images: ["image.jpg"]
enable_rapport: true
podcast:
  enabled: true
  file: "2025-01-26-podcast.mp3"
  duration: 662
  filesize: 10598327
---
```

### Step 4: Generate Transcript

Still in your newsletter directory, run:
```bash
tsb-transcript
```

This script will:
- ✅ Extract content from `index.md`
- ✅ Remove markdown formatting
- ✅ Remove images and HTML
- ✅ Create clean, plain text transcript
- ✅ Add header and footer with metadata
- ✅ Save as `transcript.txt`

Example output:
```
📝 Sunday Blender Transcript Generator
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 Title: DeepSeek Challenges AI Powerhouses
📅 Date: January 26, 2025

🔄 Generating transcript...
✅ Transcript generated: transcript.txt
📊 Statistics: 423 lines, 3847 words

✨ Transcript ready for distribution!

💡 Use cases:
  • Copy to podcast platforms (Apple Podcasts, Spotify)
  • Submit for accessibility compliance
  • Share as plain text version
  • Use for SEO optimization
```

### Step 5: Test Locally

Start your Hugo server:
```bash
hugo server -D
```

Navigate to your post and verify:
- ✅ Audio player appears at the top of the article
- ✅ Duration displays correctly
- ✅ Audio plays properly
- ✅ File loads without errors

### Step 6: Distribute Transcript

The generated `transcript.txt` can be:
- Uploaded to podcast hosting platforms
- Used for podcast episode descriptions
- Shared as accessibility content
- Used for SEO and searchability

## Directory Structure After Processing

```
content/posts/2026/20260126/
├── index.md                          ← Updated with podcast frontmatter
├── 2025-01-26-podcast.mp3           ← Converted audio file
├── transcript.txt                    ← Generated transcript
├── NotebookLM_Audio_20250126.m4a    ← Original (can be deleted)
└── [other files...]
```

## Troubleshooting

### FFmpeg Not Found
```bash
brew install ffmpeg
```

### Permission Denied
```bash
chmod +x /usr/local/bin/tsb-podcast
chmod +x /usr/local/bin/tsb-transcript
```

### Audio Not Playing on Website
- Check that the MP3 file is in the same directory as `index.md`
- Verify the filename in frontmatter matches the actual file
- Clear browser cache and reload

### Transcript Missing Content
- Check that `index.md` has valid frontmatter (between `---` markers)
- Ensure content is after the closing `---`
- Look for parsing errors in script output

## Advanced Usage

### Custom Audio File Name
If you want to manually specify the input file:
```bash
cd content/posts/2026/20260126
# Edit process_podcast.sh to accept arguments or manually convert:
ffmpeg -i your-custom-file.m4a -codec:a libmp3lame -qscale:a 2 2025-01-26-podcast.mp3
```

### Regenerate Transcript Only
If you update your article content:
```bash
cd content/posts/2026/20260126
tsb-transcript
```

## File Formats

### Audio Specifications
- **Input**: M4A (NotebookLM output)
- **Output**: MP3
  - Codec: MP3 (libmp3lame)
  - Quality: -qscale:a 2 (high quality, ~190 kbps VBR)
  - Optimized for: Web streaming

### Transcript Format
- **Format**: Plain text (.txt)
- **Encoding**: UTF-8
- **Line breaks**: Unix (LF)
- **Structure**:
  - Header with metadata
  - Clean content without markdown
  - Footer with copyright and links

## Integration with Hugo

The podcast audio player is automatically rendered when:
1. `podcast.enabled: true` in frontmatter
2. MP3 file exists in post directory
3. Hugo theme includes podcast template (already configured)

See `layouts/_default/single.html` lines 64-76 for implementation details.

## Maintenance

### Updating Scripts
Scripts are located in:
- `/Users/zire/matrix/github_zire/sundayblender/scripts/process_podcast.sh`
- `/Users/zire/matrix/github_zire/sundayblender/scripts/generate_transcript.sh`

Symlinks are at:
- `/usr/local/bin/tsb-podcast`
- `/usr/local/bin/tsb-transcript`

After updating scripts, no additional steps needed (symlinks auto-update).

## Questions?

Contact: clayton.man@sundayblender.com
