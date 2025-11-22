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

## PDF Generation

Generate PDF versions of your newsletter posts for easy sharing and archiving.

### Quick Command

From any newsletter directory (containing `index.md`), simply run:

```bash
tsb-make-pdf
```

### Prerequisites

- **Hugo development server must be running**: Run `hugo server` in a separate terminal
  - The PDF generation script loads images from `http://localhost:1313`
  - If the server isn't running, images won't display in the PDF
- **Chrome browser**: For best PDF quality (fallbacks to Safari and pandoc available)

### How It Works

1. **Find Built HTML**: Locates the Hugo-generated HTML file in `public/p/slug/index.html`
2. **Clean Content**: Removes table of contents and "Previous Issues" sections for cleaner PDF
3. **Convert to PDF**: Uses Chrome headless for high-quality conversion
4. **Smart Naming**: Generates filename like `The-Sunday-Blender-2025-09-13-Newsletter-Title.pdf`

### Complete Workflow

```bash
# 1. Start Hugo development server (in a separate terminal)
hugo server

# 2. Navigate to newsletter directory
cd content/posts/2025/09/0913

# 3. Generate PDF (while Hugo server is running)
tsb-make-pdf
```

### Output

The PDF will be saved in the same directory as your `index.md` file with a descriptive filename based on your post's title and date.

## Content Update Progress

| Date | Images | PDF | Transcript | Apple | Spotify | 小宇宙 | 喜马拉雅 | Inline 🎧 |
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