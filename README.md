# README

[![Deploy to IC Mainnet](https://github.com/Inturious-Labs/sundayblender/actions/workflows/deploy.yml/badge.svg)](https://github.com/Inturious-Labs/sundayblender/actions/workflows/deploy.yml)

The Sunday Blender's canister URL: [https://bf52x-nyaaa-aaaan-qz5aq-cai.icp0.io/](https://bf52x-nyaaa-aaaan-qz5aq-cai.icp0.io/)

## Additional Documentation

- [PLAN.md](PLAN.md) - Project roadmap and planning
- [TWITTER_BOT_README.md](TWITTER_BOT_README.md) - Twitter bot documentation

## Deploy, Test & Publish

Start Hugo's development server to view the hot-loaded site

```
hugo server
```

View the site on [//localhost:1313](http://localhost:1313) (with bind address 127.0.0.1)

To view the local site with draft content, run either of these commands:

```
hugo server --buildDrafts
hugo server -D
```

To view draft content with future dates (specific to The Sunday Blender workflow):

```
hugo server -D -F
```

When publish the site, typically you do *NOT* want to include `draft`, `future`, or `expired content`, just do:

```
hugo
```

Or to minify assets and reduce what's needed for human to understand

```
hugo --minify
```

After creating the static HTML assets in `public/` folder, `git push` the current branch to the remote:

```
git push --set-upstream origin <local_branch_name>
```

## Publishing Workflow

Complete workflow for creating and publishing a new issue of The Sunday Blender newsletter.

### 1. Create Draft Branch and Article Folder

Create a draft branch for the next issue:

```bash
git checkout -b draft/YYYYMMDD
```

Create the article folder and initialize:

```bash
mkdir -p content/posts/YYYY/MM/MMDD
cd content/posts/YYYY/MM/MMDD
tsb-init-article
```

The initializer prompts for title, slug, description, and tags, then generates `index.md` with all frontmatter fields, section headers, and links to the 3 most recent published articles.

### 2. Weekly Content Updates

Update the draft branch throughout Monday to Friday with additional stories, materials, and content refinements.

### 3. Complete Saturday Editing

Complete editing of the `index.md` file in Cursor on Saturday. Keep the `draft: true` flag in the frontmatter at this stage.

### 4. Start Hugo Development Server

Ensure Hugo development server is running for PDF generation:

```bash
hugo server -D -F
```

Keep this running in a separate terminal throughout the publishing process. The `-D` flag includes draft content and `-F` includes future-dated posts.

### 5. Generate PDF Version

Navigate to the article directory and create the PDF version:

```bash
cd content/posts/YYYY/MM/MMDD
tsb-make-pdf
```

This generates a PDF file in the same directory, which will be used for podcast creation.

### 6. Create Audio Podcast with NotebookLM

- Upload the generated PDF to [Google NotebookLM](https://notebooklm.google.com/)
- Generate an audio file (m4a format)
- Download and place the m4a file in the issue folder

### 7. Process Podcast Audio

Run the podcast processing script to:
- Convert m4a to mp3 format
- Update frontmatter fields with podcast metadata (duration, file size, etc.)

```bash
tsb-process-podcast
```

### 8. Generate Podcast Show Notes

Update the podcast RSS XML feed with enhanced show notes:

```bash
tsb-generate-shownotes
```

This creates AI-enhanced show notes with structured sections (Overview, Key Topics, Notable Quotes, etc.) in the RSS feed.

### 9. Finalize and Push Changes

- Change `draft: false` in the frontmatter
- Commit all changes:

```bash
git add content/posts/YYYY/MM/MMDD/
git commit -m "Add YYYY-MM-DD issue with podcast and show notes"
git push --set-upstream origin draft/YYYYMMDD
```

### 10. Create Pull Request

Create a PR to merge the commits into `main`, which triggers the GitHub Actions deploy workflow to Internet Computer (IC) mainnet.

### 11. Merge and Clean Up Remote

- Merge the PR on GitHub
- Delete the remote draft branch after successful merge

### 12. Update Local Main Branch

Switch to main and pull the latest changes:

```bash
git checkout main
git pull
```

### 13. Delete Local Draft Branch

Clean up the local draft branch:

```bash
git branch -d draft/YYYYMMDD
```

### 14. Post Announcement Tweet

Post an announcement tweet on [@SundayBlender](https://x.com/SundayBlender) to announce the new issue:

- Log in to X.com with the @SundayBlender account
- Compose a tweet announcing the new issue with the article link
- Include relevant hashtags and a brief teaser about the content
- Attach the featured image if applicable

### 15. Schedule Twitter Bot

Initiate the Twitter bot schedule script to promote the new issue across social media.

On Dalaran, run the interactive scheduler:

```bash
./scripts/schedule_tweets.sh
```

Refer to [TWITTER_BOT_README.md](TWITTER_BOT_README.md) for detailed Twitter bot instructions.

### 16. Update Content Update Progress Chart

Update the "Content Update Progress" table in the README with the new issue status. Mark completed items with 🟢 and incomplete items with 🔴:

- Images: 🟢 (if images are included)
- PDF: 🟢 (PDF was generated in step 5)
- Show Notes: 🟢 (show notes were generated in step 8)
- Apple: 🟢 (if uploaded to Apple Podcasts)
- Spotify: 🟢 (if uploaded to Spotify)
- 小宇宙: 🟢 (if uploaded to Xiaoyuzhou)
- 喜马拉雅: 🔴 (or 🟢 if uploaded)
- Inline 🎧: 🟢 (podcast is inline in the post)

## Content Update Progress

| Date | Images | PDF | Show Notes | Apple | Spotify | 小宇宙 | 喜马拉雅 | Inline 🎧 |
|------|:------:|:---:|:----------:|:-----:|:-------:|:------:|:--------:|:---------:|
| [2025-11-15](https://weekly.sundayblender.com/p/the-return-of-chinese-rock-in-kuala-kumpur/) | 🟢 | 🟢 | 🔴 | 🟢 | 🟢 | 🟢 | 🔴 | 🟢 |
| [2025-11-08](https://weekly.sundayblender.com/p/who-wins-in-this-ai-bonanza/) | 🟢 | 🟢 | 🔴 | 🟢 | 🟢 | 🟢 | 🔴 | 🟢 |
| [2025-11-01](https://weekly.sundayblender.com/p/when-yang-meets-yang-celebrating-life-at-the-peak-of-autumn/) | | | | | | | | |
| [2025-10-25](https://weekly.sundayblender.com/p/the-greatest-performance-in-baseball-history/) | | | | | | | | |
| [2025-10-11](https://weekly.sundayblender.com/p/djokovic-falls-to-vacherot-at-2025-shanghai-masters/) | | | | | | | | |
| [2025-09-27](https://weekly.sundayblender.com/p/1500x-acceleration-from-ford-model-to-to-byd-yangwang-u9-extreme/) | | | | | | | | |
| [2025-09-20](https://weekly.sundayblender.com/p/all-you-need-is-another-ai-research-report/) | | | | | | | | |
| [2025-09-13](https://weekly.sundayblender.com/p/good-old-apple-strikes-back/) | | | | | | | | |
| [2025-07-06](https://weekly.sundayblender.com/p/while-young-talents-trailblaze-ai-frontier-legendary-icons-write-new-chapters/) | | | | | | | | |
| [2025-06-28](https://weekly.sundayblender.com/p/flying-without-wings-seeing-without-eyes-and-driving-without-humans/) | | | | | | | | |
| [2025-06-21](https://weekly.sundayblender.com/p/cyber-doomsday-meets-ai-boomtown/) | | | | | | | | |
| [2025-06-15](https://weekly.sundayblender.com/p/from-labubu-viral-craze-to-glaciers-spiral-of-doom/) | | | | | | | | |
| [2025-06-07](https://weekly.sundayblender.com/p/every-dog-has-its-day/) | | | | | | | | |
| [2025-05-31](https://weekly.sundayblender.com/p/when-ai-swung-a-racket-and-nadal-hung-up-his/) | | | | | | | | |
| [2025-05-24](https://weekly.sundayblender.com/p/shining-stars-of-the-last-generation/) | | | | | | | | |
| [2025-05-17](https://weekly.sundayblender.com/p/ai-advances-scientific-discovery/) | | | | | | | | |
| [2025-05-10](https://weekly.sundayblender.com/p/blaze-of-glory-and-sound-of-silence/) | | | | | | | | |
| [2025-05-09](https://weekly.sundayblender.com/p/we-come-this-far-now-what/) | | | | | | | | |
| [2025-05-03](https://weekly.sundayblender.com/p/hello-darkness-my-old-friend/) | | | | | | | | |
| [2025-04-26](https://weekly.sundayblender.com/p/a-tale-of-two-nations/) | | | | | | | | |
| [2025-04-20](https://weekly.sundayblender.com/p/flying-dutchman-sails-away/) | | | | | | | | |
| [2025-04-05](https://weekly.sundayblender.com/p/the-world-jitters-but-nintendo-glitters/) | | | | | | | | |
| [2025-03-29](https://weekly.sundayblender.com/p/the-charming-arrival-of-agi/) | | | | | | | | |
| [2025-03-22](https://weekly.sundayblender.com/p/march-madness-to-mars/) | | | | | | | | |
| [2025-03-16](https://weekly.sundayblender.com/p/space-oddities-on-the-moon-space/) | | | | | | | | |
| [2025-03-09](https://weekly.sundayblender.com/p/the-end-game-for-technology/) | | | | | | | | |
| [2025-03-02](https://weekly.sundayblender.com/p/ancient-water-on-mars/) | | | | | | | | |
| [2025-02-24](https://weekly.sundayblender.com/p/meeting-of-the-minds/) | | | | | | | | |
| [2025-02-16](https://weekly.sundayblender.com/p/mega-snow-and-mega-collision/) | | | | | | | | |
| [2025-02-09](https://weekly.sundayblender.com/p/chinese-film-ne-zha-2-shattered-record/) | | | | | | | | |
| [2025-02-01](https://weekly.sundayblender.com/p/an-exuberant-chinese-new-year/) | | | | | | | | |
| [2025-01-30](https://weekly.sundayblender.com/p/make-news-interesting-for-kids/) | | | | | | | | |
| [2025-01-26](https://weekly.sundayblender.com/p/deepseek-challenges-ai-powerhouses/) | | | | | | | | |