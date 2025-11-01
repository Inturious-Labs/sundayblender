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

## Link Validation with htmltest

This project uses [htmltest](https://github.com/wjdp/htmltest) to validate internal links and ensure a healthy site structure.

### Setup

1. **Install htmltest** (if not already installed):
   ```bash
   # macOS
   brew install htmltest
   
   # Linux
   wget https://github.com/wjdp/htmltest/releases/latest/download/htmltest_linux_amd64.tar.gz
   tar -xzf htmltest_linux_amd64.tar.gz
   sudo mv htmltest /usr/local/bin/
   ```

2. **Configuration**: The project includes a `.htmltest.yml` file configured for Hugo sites:
   - Checks internal links only (skips external URLs for speed)
   - Ignores development artifacts (livereload.js, etc.)
   - Validates mailto links
   - Checks internal hash links

### Usage

**Basic Link Check**
```bash
# Build the site first
hugo

# Check public/ folder directly
htmltest

# Check all internal links
htmltest public/ --conf .htmltest.yml
```

**Skip External Links (Faster)**
```bash
htmltest public/ --skip-external
```

**Save Results to File**
```bash
htmltest public/ --conf .htmltest.yml --output-path link-check-results.log
```

**Check with Verbose Output**
```bash
htmltest public/ --conf .htmltest.yml --log-level 2
```

### What It Checks

✅ **Internal Links**: All links within your site
✅ **Hash Links**: Internal page anchors (e.g., `#section`)
✅ **Mailto Links**: Email address validation
✅ **Image Alt Text**: Missing alt attributes
❌ **External Links**: Skipped for faster execution

### Integration with Workflow

**Pre-Deployment Check**
```bash
# Build and test before deploying
hugo
htmltest public/ --conf .htmltest.yml

# If no errors, proceed with deployment
git add .
git commit -m "Update site"
git push
```

**CI/CD Integration**
```bash
# For automated testing
hugo --minify
htmltest public/ --conf .htmltest.yml --output-json results.json
```

## Newsletter Sign-up Implementation

This Hugo site includes a complete newsletter sign-up system that integrates with your Buttondown service (`sundayblender`).

### How It Works

The newsletter sign-up form automatically appears on:
- **Individual blog posts** (after the content)
- **Dedicated newsletter page** (`/subscribe/`)

### Usage Options

**1. Automatic Placement (Default)**
The newsletter form automatically appears on all pages unless disabled. To hide it on a specific page, add this to the front matter:

```yaml
---
title: "Your Post Title"
hideNewsletter: true
---
```

**2. Manual Placement with Shortcodes**
You can manually place the newsletter form anywhere in your content using shortcodes:

```markdown
{{< newsletter >}}
```

**3. Dedicated Newsletter Page**
A dedicated newsletter page is available at `/subscribe/` with:
- Detailed benefits of subscribing
- Privacy information
- Professional sign-up form

### Buttondown Integration

The forms are configured to work with your Buttondown service:
- **Endpoint**: `https://buttondown.com/api/emails/embed-subscribe/sundayblender`
- **Method**: POST
- **Target**: Opens in new tab for completion

### Files Created

1. **`layouts/partials/newsletter-signup.html`** - Main newsletter form
2. **`layouts/shortcodes/newsletter.html`** - Shortcode for full form
3. **`layouts/_default/newsletter.html`** - Dedicated newsletter page template
4. **`content/subscribe.md`** - Subscribe page content

### Testing


### Privacy & Compliance

The newsletter forms include:
- Clear privacy messaging
- Unsubscribe information
- GDPR-compliant language
- No unnecessary data collection

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

## Data Management & Backup

### Email List Backup

The `data/` folder serves as a backup repository for your newsletter subscriber list and other important data.

#### Current Data Files

**`substack_export_emails.csv`**
- **Purpose**: Backup of newsletter subscriber emails from Substack export
- **Content**: CSV file containing subscriber email addresses
- **Usage**: Periodic backup of your current subscriber base
- **Privacy**: Contains only email addresses, no personal information

#### Backup Strategy

**Periodic Backups**
- Export current subscriber list from Buttondown monthly
- Store in `data/` folder with descriptive filename
- Include date in filename for version tracking
- Example: `buttondown_emails_2025_01.csv`

**File Naming Convention**
```
data/
├── substack_export_emails.csv          # Original Substack export
├── buttondown_emails_2025_01.csv      # January 2025 backup
├── buttondown_emails_2025_02.csv      # February 2025 backup
└── ...
```