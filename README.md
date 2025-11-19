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

| Date | Images | PDF | Transcript | Apple Podcast | Spotify | 小宇宙 | 喜马拉雅 |
|------|--------|-----|------------|---------------|---------|--------|----------|
| 2025-11-15 | | | | | | | |
| 2025-11-08 | | | | | | | |
| 2025-11-01 | | | | | | | |
| 2025-10-25 | | | | | | | |
| 2025-10-11 | | | | | | | |
| 2025-09-27 | | | | | | | |
| 2025-09-20 | | | | | | | |
| 2025-09-13 | | | | | | | |
| 2025-07-06 | | | | | | | |
| 2025-06-28 | | | | | | | |
| 2025-06-21 | | | | | | | |
| 2025-06-15 | | | | | | | |
| 2025-06-07 | | | | | | | |
| 2025-05-31 | | | | | | | |
| 2025-05-24 | | | | | | | |
| 2025-05-17 | | | | | | | |
| 2025-05-10 | | | | | | | |
| 2025-05-09 | | | | | | | |
| 2025-05-03 | | | | | | | |
| 2025-04-26 | | | | | | | |
| 2025-04-20 | | | | | | | |
| 2025-04-05 | | | | | | | |
| 2025-03-29 | | | | | | | |
| 2025-03-22 | | | | | | | |
| 2025-03-16 | | | | | | | |
| 2025-03-09 | | | | | | | |
| 2025-03-02 | | | | | | | |
| 2025-02-24 | | | | | | | |
| 2025-02-16 | | | | | | | |
| 2025-02-09 | | | | | | | |
| 2025-02-01 | | | | | | | |
| 2025-01-30 | | | | | | | |
| 2025-01-26 | | | | | | | |