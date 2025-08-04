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

## Lazy Loading Implementation

This Hugo site has automatic lazy loading implemented using the native `loading="lazy"` attribute, which is supported by all modern browsers.

### How It Works

**Automatic Lazy Loading**
- All images in your markdown content automatically get `loading="lazy"` added
- The render hook (`layouts/_default/_markup/render-image.html`) handles this automatically
- No need to manually add attributes to your images

**Image Optimization**
- Images maintain their original sizes (up to 1200px as per image processing workflow)
- Responsive styling ensures images scale properly on all devices
- Fallback for external images

**Error Handling**
- Failed images are hidden gracefully
- Console warnings for debugging
- No broken image placeholders

### Usage

**In Markdown Content**
Simply use regular markdown image syntax:

```markdown
![Alt text](image.jpg)
```

The render hook automatically adds:
- `loading="lazy"`
- `decoding="async"`
- Error handling
- Responsive sizing

**Using the Shortcode (Optional)**
For more control, you can use the custom shortcode:

```markdown
{{< img src="image.jpg" alt="Alt text" class="custom-class" >}}
```

### Benefits

1. **Performance**: Images only load when they're about to enter the viewport
2. **Bandwidth**: Saves data for users on slow connections
3. **SEO**: Better Core Web Vitals scores
4. **User Experience**: Faster page loads, especially on mobile

### Browser Support

- **Chrome**: 76+ ✅
- **Firefox**: 75+ ✅
- **Safari**: 15.4+ ✅
- **Edge**: 79+ ✅

For older browsers, images load normally without lazy loading.

### Testing

**Method 1: Browser Dev Tools (Recommended)**
1. Open browser dev tools (F12)
2. Go to Network tab
3. Enable "Slow 3G" or "Fast 3G" throttling
4. Scroll down the page
5. Watch images load as you scroll

**Method 2: Network Throttling**
1. In Chrome Dev Tools → Network tab
2. Click the "No throttling" dropdown
3. Select "Slow 3G" or "Fast 3G"
4. Refresh the page and scroll

### Customization

**CSS Styling**
Edit `themes/diary/static/css/lazy-loading.css` to customize:
- Loading animations
- Image styling
- Error states

**JavaScript Enhancement**
The base template includes a simple script that:
- Adds lazy loading to any images without it
- Provides error handling
- Can be extended for custom functionality