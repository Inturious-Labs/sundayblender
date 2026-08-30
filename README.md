# README

The Sunday Blender newsletter: [https://weekly.sundayblender.com/](https://weekly.sundayblender.com/) (deployed via Vercel)

## Additional Documentation

- [PLAN.md](docs/PLAN.md) - Project roadmap and planning
- [TWITTER_BOT_README.md](docs/TWITTER_BOT_README.md) - Twitter bot documentation

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
mkdir -p content/posts/YYYY/MMDD
cd content/posts/YYYY/MMDD
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

**Picking images for a whole issue (recommended):**

`tsb-image-picker` finds candidates for every story at once and lets you choose
them from a single page, instead of searching for each one by hand:

```bash
tsb-image-picker --issue MMDD
```

It reads the draft, works out a search query per story, fetches three
candidates each (about a minute for a full issue), then opens
`http://localhost:8420`. Each screen shows one story with its three options.
Click one and it is downloaded, normalized to the usual JPEG ≤1200px / ≤500KB,
saved into the issue folder, and written into `index.md` above the story —
then it moves to the next.

Per story you can also edit the search query, press **↻ More** for three
different candidates, or **Skip** and come back later. Keys: `1`/`2`/`3` to
pick, `r` for more, `s` to skip, `←`/`→` to move between stories.

Images come from Brave (current news photos; needs `BRAVE_API_KEY` in
`~/.secrets`), plus Wikimedia Commons and Openverse for older subjects. The
source and licence are shown under every thumbnail, and stock-library images
that usually arrive watermarked are marked `watermark?` — worth avoiding.

Nothing is written until you click, and every change lands in `index.md`, so
`git diff` shows exactly what happened.

**Fetching a single image by URL:**

For one-off images — a replacement, or something the picker could not find —
`tsb-fetch-image` takes a URL copied from Google Images and normalizes it in a
single step (caps it at 1200px wide and ≤500KB so the site loads fast):

1. In Google Images, click the result to open the large preview.
2. Right-click the **large image** → **Copy image address**
   (this is the direct image URL — *not* the search-result link, which only
   points to the web page the image sits on and cannot be used).
3. Run, pasting the URL in quotes:

```bash
tsb-fetch-image --issue MMDD "<image-url>"
# or, when already inside the issue folder, the destination is auto-detected:
cd content/posts/YYYY/MMDD
tsb-fetch-image "<image-url>" [optional-name]
```

The image lands in the issue folder as a JPEG, ≤1200px wide, ≤500KB. Without
`--issue` and when run outside an issue folder, it saves to `~/Downloads/`.
If you paste a Google thumbnail (`gstatic.com`) or a page link by mistake,
the script detects it and tells you to re-copy the image address.

### 3. Audit Text Content

Run a text audit to ensure the article is ready for PDF generation:

```bash
cd content/posts/YYYY/MMDD
tsb-audit-text
```

This verifies frontmatter fields, images, section content, and reading time before proceeding to PDF/podcast generation.

### 4. Generate PDF Version

Ensure Hugo dev server is running (`hugo server -D -F`), then generate the PDF:

```bash
cd content/posts/YYYY/MMDD
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
cd content/posts/YYYY/MMDD
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
cd content/posts/YYYY/MMDD
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
git add content/posts/YYYY/MMDD/
git commit -m "Publish YYYY-MM-DD issue"
git push --set-upstream origin draft/YYYYMMDD
```

### 7. Create PR, Merge, and Clean Up

- Create a PR to merge `draft/YYYYMMDD` into `main`
- This triggers Vercel auto-deployment to production
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

## Scripts Reference

All scripts live in `scripts/` and are exposed as `tsb-*` commands via
symlinks in `/usr/local/bin/` (so they run from anywhere). The convention for
most of them is to `cd` into the issue folder (`content/posts/YYYY/MMDD/`)
first.

| Command | Script | What it does |
|---------|--------|--------------|
| `tsb-init-article` | `init_article.py` | Generates `index.md` for a new issue with frontmatter placeholders, section headers, and links to the 3 most recent published articles. Run from inside the new issue folder. |
| `tsb-image-picker` | `image_picker.py` | Finds three image candidates for every story in an issue and serves a local page (`localhost:8420`) to pick from. The chosen image is downloaded, normalized, and inserted into `index.md`. Searches Brave (needs `BRAVE_API_KEY`), Wikimedia Commons, and Openverse. See [Weekly Content Updates](#2-weekly-content-updates). |
| `tsb-fetch-image` | `fetch_image.sh` | Downloads an image from a Google Images "Copy image address" URL and normalizes it to JPEG, ≤1200px wide, ≤500KB. Saves into the issue folder (`--issue MMDD` or auto-detected) or `~/Downloads/`. See [Weekly Content Updates](#2-weekly-content-updates). |
| `tsb-audit-text` | `audit_text.py` | Pre-flight text audit — verifies frontmatter fields, images, section content, and reading time before PDF/podcast generation. |
| `tsb-make-pdf` | `html_to_pdf.py` | Renders the article (from the running Hugo dev server) to a PDF in the issue folder, used as the podcast source. Versions previous PDFs rather than overwriting. |
| `tsb-make-podcast` | `process_podcast.py` | Converts the NotebookLM `m4a` to `YYYY-MM-DD-podcast.mp3`, updates podcast frontmatter (`enabled`, `file`, `duration`, `filesize`), and regenerates show notes. |
| `tsb-audit-final` | `audit_final.py` | Final pre-publish gate — checks `draft: false`, PDF/MP3 presence, podcast frontmatter, Twitter card tags, hero image, and both RSS feeds. |
| `tsb-update-progress` | `update_progress.py` | Updates the Content Update Progress table below by checking the production site/RSS. Flags: `--sync`, `--date YYYY-MM-DD`, `--all`, `--dry-run`. |

The following `scripts/` files are **not** wired as `tsb-*` commands and are
run directly or by other tooling:

| Script | What it does |
|--------|--------------|
| `image_process.sh` | Batch-renames and resizes **already-downloaded** images in a directory (lowercase, ≤10-char names, ≤1200px wide). Complements `tsb-fetch-image`, which handles single-image fetch + normalize. |
| `schedule_tweets.sh` / `post_scheduled_tweets.py` / `run_twitter_bot.sh` | Twitter announcement bot — run on Dalaran. See [TWITTER_BOT_README.md](docs/TWITTER_BOT_README.md). |
| `evening-push.sh` | Auto-pushes the current draft branch (if it has unpushed commits) to keep Moonglade in sync; logs to `scripts/push.log`. Typically run on a schedule. |

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