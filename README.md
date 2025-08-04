# README

The Sunday Blender's canister URL: [https://bf52x-nyaaa-aaaan-qz5aq-cai.icp0.io/](https://bf52x-nyaaa-aaaan-qz5aq-cai.icp0.io/)

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

## Image Processing Workflow

This project includes an automated image processing workflow to optimize images for web publishing while maintaining quality and performance.

### Workflow Steps:

1. **Image Collection**: Author grabs images from various online resources and saves them into the post's subfolder under `content/posts/YYYY/MM/DDDD/`

2. **Draft Linking**: Link images into the `index.md` during draft stage using standard Markdown syntax:
   ```markdown
   ![Alt text](image_filename.jpg)
   ```

3. **Image Processing**: When draft is complete and ready for publishing, run the image processing script:
   ```bash
   ./scripts/image_process.sh content/posts/YYYY/MM/DDDD/
   ```

   The script will:
   - Convert filenames to lowercase
   - Replace spaces with underscores
   - Truncate filenames to 10 characters maximum
   - Resize images to max width of 1200px (maintaining aspect ratio)
   - Display a comprehensive summary with before/after comparison

4. **Link Updates**: After processing, update the image links in `index.md` to match the new filenames. The script provides a detailed summary showing the original and new filenames.

### Example:

**Before processing:**
```
content/posts/2025/01/0126/
├── index.md
├── LA_fire.webp
├── cofee table.jpg
├── lakersandwarriors.jpg
└── ...
```

**After processing:**
```
content/posts/2025/01/0126/
├── index.md
├── la_fire.webp
├── cofee_tabl.jpg
├── lakersandw.jpg
└── ...
```

### Script Features:

- **Automatic resizing**: Images wider than 1200px are automatically resized
- **File size optimization**: Reduces file sizes while maintaining quality
- **Duplicate handling**: Automatically adds numbers to prevent filename conflicts
- **Comprehensive reporting**: Shows total size savings and individual file changes
- **Safe processing**: Asks for confirmation before making changes