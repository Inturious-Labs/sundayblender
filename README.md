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

The initializer generates `index.md` with all frontmatter fields (with placeholders), section headers, and links to the 3 most recent published articles.

### 2. Weekly Content Updates

Update the article throughout the week with additional stories, materials, and content refinements.

- Make all changes in the `draft/YYYYMMDD` branch, NOT the `main` branch
- Keep `draft: true` in frontmatter throughout the week
- Commit changes locally, but no need to push to remote until ready to publish
- Preview with `hugo server -D -F` to display draft articles with future dates
- For Cursor editor, use theme `Quiet Light` for better readability

### 3. Audit Text Content

Run a text audit to ensure the article is ready for PDF generation:

```bash
cd content/posts/YYYY/MM/MMDD
tsb-audit-text
```

This verifies frontmatter fields, images, section content, and reading time before proceeding to PDF/podcast generation.

### 4. Generate PDF Version

Ensure Hugo dev server is running (`hugo server -D -F`), then generate the PDF:

```bash
cd content/posts/YYYY/MM/MMDD
tsb-make-pdf
```

This generates a PDF in the article folder for podcast creation. If run again, it creates `name_01.pdf`, `name_02.pdf`, etc. without overwriting previous versions. However, `static/pdf/` always gets the latest version with the original filename (overwrites older versions).

### 5. Create and Process Podcast

**Generate audio:**
- Upload the PDF to [Google NotebookLM](https://notebooklm.google.com/)
- Use `Audio Overview` and select `Deep Dive` mode
- Download the `m4a` file to the article folder

**Process audio:**
```bash
cd content/posts/YYYY/MM/MMDD
tsb-make-podcast
```

This single command:

- Converts `m4a` to `mp3` and name that as `YYYY-MM-DD-podcast.mp3`
- Updates frontmatter: `enabled: true`, `file`, `duration`, `filesize`
- Regenerates `shownotes` with the actual description

### 6. Final Audit and Push

**Step 1:** Change `draft: false` in the frontmatter

**Step 2:** Run final audit to verify everything is ready:

```bash
cd content/posts/YYYY/MM/MMDD
tsb-audit-final
```

This checks:

- draft is set to `false`
- PDF and MP3 files exist
- Podcast frontmatter is complete (enabled, duration, filesize)
- Twitter card meta tags are correct (`summary_large_image`)
- Hero image is displayed
- Main RSS feed includes the article
- Podcast RSS feed includes the episode

**Step 3:** Commit and push:

```bash
git add content/posts/YYYY/MM/MMDD/
git commit -m "Publish YYYY-MM-DD issue"
git push --set-upstream origin draft/YYYYMMDD
```

### 7. Create PR, Merge, and Clean Up

- Create a PR to merge `draft/YYYYMMDD` into `main`
- This triggers the GitHub deploy action to deploy the production canister on the Internet Computer
- Once the merge is completed, the remote draft branch is deleted automatically
- Update local:

```bash
git checkout main
git pull
git branch -d draft/YYYYMMDD
```

### 8. Post Announcement Tweet

Post an announcement tweet on [@SundayBlender](https://x.com/SundayBlender) to announce the new issue:

- Log in to X.com with the `@SundayBlender` account
- Compose a tweet announcing the new issue with the article link
- Include relevant hashtags and a brief teaser about the content
- Attach the featured image if applicable

### 9. Schedule Twitter Bot

Initiate the Twitter bot schedule script to promote the new issue across social media.

On Dalaran, update the `main` branch there and then run the interactive scheduler:

```bash
ssh dalaran
cd sundayblender
git pull
./scripts/schedule_tweets.sh
```

Refer to [TWITTER_BOT_README.md](TWITTER_BOT_README.md) for detailed Twitter bot instructions.

### 10. Update Content Update Progress Chart

Run the progress checker to automatically update the table:

```bash
cd matrix/github_zire/sundayblender
tsb-update-progress
```

Options:

- `--sync` - Add new articles from production RSS (no status check)
- `--date YYYY-MM-DD` - Check specific article
- `--all` - Check all articles in table
- `--dry-run` - Show results without updating

The script automatically discovers and adds new articles from the production site.

Note: 喜马拉雅 (Ximalaya) requires manual verification.

## Content Update Progress

| Date | Images | PDF | Show Notes | Apple | Spotify | 小宇宙 | 喜马拉雅 | Inline 🎧 |
|------|:------:|:---:|:----------:|:-----:|:-------:|:------:|:--------:|:---------:|
| [2025-11-22](https://weekly.sundayblender.com/p/the-most-intelligent-ai-model-yet/) |  |  |  |  |  |  |  |  |
| [2025-11-29](https://weekly.sundayblender.com/p/who-will-lead-brazil-at-2026-world-cup-neymay-or-estevao/) |  |  |  |  |  |  |  |  |
| [2025-11-15](https://weekly.sundayblender.com/p/the-return-of-chinese-rock-in-kuala-kumpur/) | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 |  | 🟢 |
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