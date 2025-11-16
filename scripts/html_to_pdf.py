#!/usr/bin/env python3
"""
HTML to PDF Converter for Sunday Blender Newsletter
Converts the built Hugo HTML page to PDF
"""

import os
import sys
import re
import subprocess
import shutil
import time
import threading
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup

def show_progress(message, stop_event):
    """Show animated progress indicator"""
    spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    i = 0
    while not stop_event.is_set():
        print(f'\r{spinner[i % len(spinner)]} {message}', end='', flush=True)
        i += 1
        time.sleep(0.1)

def find_newsletter_html(working_dir):
    """Find the built HTML file for the newsletter"""
    working_path = Path(working_dir)

    # Look for index.md to get the slug
    index_md = working_path / "index.md"
    if not index_md.exists():
        raise FileNotFoundError(f"index.md not found in {working_dir}")

    # Read frontmatter to get slug
    with open(index_md, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract slug from frontmatter
    slug_match = re.search(r'^slug:\s*(.+?)\s*$', content, re.MULTILINE)
    if not slug_match:
        raise ValueError("No slug found in frontmatter")

    slug = slug_match.group(1).strip().strip('"\'')  # Strip quotes and whitespace

    # Look for the built HTML file - navigate to project root
    # From content/posts/2025/09/0913 -> go up to sundayblender root (5 levels up)
    project_root = working_path.parent.parent.parent.parent.parent
    html_path = project_root / "public" / "p" / slug / "index.html"


    if not html_path.exists():
        raise FileNotFoundError(f"Built HTML file not found at {html_path}")

    return html_path

def get_pdf_name(working_dir):
    """Generate PDF filename from frontmatter"""
    working_path = Path(working_dir)
    index_md = working_path / "index.md"

    with open(index_md, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract title and date
    title_match = re.search(r'^title:\s*["\']?(.*?)["\']?\s*$', content, re.MULTILINE)
    date_match = re.search(r'^date:\s*(.*?)\s*$', content, re.MULTILINE)

    title = title_match.group(1).strip() if title_match else "Newsletter"
    date = date_match.group(1).strip() if date_match else ""

    # Clean title for filename
    clean_title = title.replace(' ', '-').replace('"', '').replace("'", "").replace(',', '-')
    clean_title = re.sub(r'[<>:"/\\|?*]', '', clean_title)
    # Remove consecutive hyphens
    clean_title = re.sub(r'-+', '-', clean_title)

    return f"The-Sunday-Blender-{date}-{clean_title}.pdf"

def get_base_url(working_dir):
    """Get base URL from Hugo config"""
    try:
        # Find Hugo root and read config
        current_dir = Path(working_dir).resolve()
        for parent in [current_dir] + list(current_dir.parents):
            hugo_config = parent / 'hugo.toml'
            if hugo_config.exists():
                with open(hugo_config, 'r', encoding='utf-8') as f:
                    config_content = f.read()

                # Extract baseURL
                url_match = re.search(r"baseURL\s*=\s*['\"](.+?)['\"]", config_content)
                if url_match:
                    return url_match.group(1).rstrip('/')
                break

        return "weekly.sundayblender.com"  # fallback
    except:
        return "weekly.sundayblender.com"  # fallback

def get_header_info(working_dir):
    """Extract header information from frontmatter"""
    working_path = Path(working_dir)
    index_md = working_path / "index.md"

    with open(index_md, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract title, featured image, and date
    title_match = re.search(r'^title:\s*["\']?(.*?)["\']?\s*$', content, re.MULTILINE)
    featured_match = re.search(r'^featured_image:\s*["\']?(.*?)["\']?\s*$', content, re.MULTILINE)
    date_match = re.search(r'^date:\s*(.*?)\s*$', content, re.MULTILINE)

    title = title_match.group(1).strip() if title_match else "Newsletter Issue"
    featured_image = featured_match.group(1).strip() if featured_match else ""
    date = date_match.group(1).strip() if date_match else ""

    return {
        'title': title,
        'featured_image': featured_image,
        'date': date
    }

def clean_html_for_pdf(html_path, working_dir):
    """Remove unwanted sections and optimize HTML for A4 print PDF"""
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, 'html.parser')

    # Get header information
    header_info = get_header_info(working_dir)

    # Get base URL from Hugo config
    base_url = get_base_url(working_dir)

    # Add print-friendly CSS styles
    # Get the absolute path to the featured image in the built HTML directory
    if header_info['featured_image']:
        # Extract directory from html_path to get the built directory
        html_dir = Path(html_path).parent
        featured_image_path = html_dir / header_info['featured_image']
        featured_image_url = f"file://{featured_image_path}"
    else:
        featured_image_url = ""
    print_css = """
    <style type="text/css" media="print">
    @page {
        size: A4;
        margin: 0.3in 0.3in 0.8in 0.3in;
        @bottom-left {
            content: "© 2025 Clayton Man";
            font-family: 'Arial', sans-serif;
            font-size: 10px;
            color: #666;
        }
        @bottom-center {
            content: counter(page) "/" counter(pages);
            font-family: 'Arial', sans-serif;
            font-size: 12px;
            color: #666;
        }
        @bottom-right {
            content: """ + f'"{base_url}"' + """;
            font-family: 'Arial', sans-serif;
            font-size: 10px;
            color: #666;
        }
    }

    body {
        font-family: 'Georgia', serif;
        font-size: 20px !important;
        line-height: 1.6 !important;
        color: #000 !important;
        background: white !important;
        margin: 0 !important;
        padding: 0 !important;
        width: 100% !important;
        max-width: none !important;
    }

    .magazine-header {
        width: 100% !important;
        height: 4in !important;
        position: relative !important;
        margin: 0 0 0.3in 0 !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        align-items: center !important;
        page-break-inside: avoid !important;
        overflow: hidden !important;
    }

    .magazine-header .background-image {
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        width: 100% !important;
        height: 100% !important;
        object-fit: cover !important;
        z-index: 0 !important;
    }

    .magazine-header::before {
        content: "" !important;
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        bottom: 0 !important;
        background: rgba(0, 0, 0, 0.7) !important;
        z-index: 1 !important;
    }

    .header-content {
        position: relative !important;
        z-index: 2 !important;
        text-align: center !important;
        color: white !important;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8) !important;
    }

    .newsletter-name {
        font-family: 'Times New Roman', serif !important;
        font-size: 48px !important;
        font-weight: bold !important;
        margin: 0 0 10px 0 !important;
        letter-spacing: 2px !important;
        text-transform: uppercase !important;
        border-top: 3px solid white !important;
        border-bottom: 3px solid white !important;
        padding: 15px 0 !important;
        line-height: 1.1 !important;
    }

    .issue-title {
        font-family: 'Georgia', serif !important;
        font-size: 28px !important;
        font-weight: normal !important;
        font-style: italic !important;
        margin: 15px auto 0 auto !important;
        letter-spacing: 1px !important;
        max-width: 80% !important;
        line-height: 1.3 !important;
        text-align: center !important;
        width: 100% !important;
    }

    .issue-date {
        font-family: 'Georgia', serif !important;
        font-size: 18px !important;
        font-weight: normal !important;
        font-style: italic !important;
        margin: 10px auto 0 auto !important;
        letter-spacing: 1px !important;
        max-width: 80% !important;
        line-height: 1.3 !important;
        text-align: center !important;
        width: 100% !important;
        color: white !important;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8) !important;
    }

    .content-wrapper {
        column-count: 2;
        column-gap: 0.5in;
        column-rule: 1px solid #ddd;
        column-fill: balance;
        text-align: justify;
        word-wrap: break-word;
        hyphens: auto;
        overflow-wrap: break-word;
        padding: 0 !important;
        margin: 0 !important;
        width: 100% !important;
        box-sizing: border-box !important;
    }

    h1 {
        font-size: 24px !important;
        margin-bottom: 16px !important;
        column-span: all;
        text-align: center;
        border-bottom: 2px solid #000;
        padding-bottom: 8px;
    }

    h2 {
        font-size: 20px !important;
        margin: 20px 0 12px 0 !important;
        font-weight: bold !important;
        break-after: avoid;
        text-transform: uppercase !important;
        letter-spacing: 1.5px !important;
        background: linear-gradient(135deg, #8B4513 0%, #ffffff 100%) !important;
        color: #000 !important;
        padding: 8px 12px !important;
        text-align: center !important;
        border-radius: 3px !important;
        font-family: 'Arial', sans-serif !important;
    }

    h3 {
        font-size: 18px !important;
        margin: 16px 0 10px 0 !important;
        font-weight: bold !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        border-bottom: 3px solid #000 !important;
        padding-bottom: 4px !important;
        font-family: 'Arial', sans-serif !important;
    }

    p {
        font-size: 20px !important;
        line-height: 1.6 !important;
        margin-bottom: 12px !important;
        orphans: 2;
        widows: 2;
        word-wrap: break-word !important;
        hyphens: auto !important;
        overflow-wrap: break-word !important;
    }

    img {
        max-width: 100% !important;
        height: auto !important;
        display: block !important;
        margin: 12px auto !important;
        border: 1px solid #ddd;
        break-inside: avoid;
    }

    /* Make images fit within column width */
    .content img,
    article img,
    main img {
        max-width: 100% !important;
        width: auto !important;
        height: auto !important;
        max-height: 3in !important;
    }

    /* Avoid breaking articles across columns when possible */
    article, section {
        break-inside: avoid-column;
        margin-bottom: 16px;
    }

    /* Hide any navigation, footer, sidebar elements */
    nav, aside, .sidebar, .navigation, .menu, .footer {
        display: none !important;
    }

    /* Hide header metadata elements */
    .tags, .tag-list, .post-tags, .article-tags,
    .description, .post-description, .excerpt, .summary,
    .meta, .post-meta, .article-meta, .metadata,
    .author, .byline, .post-author,
    .date, .publish-date, .post-date,
    .reading-time, .read-time, .time-to-read,
    .breadcrumb, .breadcrumbs,
    .share, .sharing, .social-share,
    .category, .categories, .post-category,
    .lead, .intro, .subtitle, .subheading {
        display: none !important;
    }

    /* Hide elements by common class patterns */
    [class*="tag"], [class*="meta"], [class*="author"],
    [class*="date"], [class*="share"], [class*="social"],
    [class*="breadcrumb"], [class*="category"],
    [class*="description"], [class*="excerpt"],
    [class*="reading"], [class*="time"],
    [class*="summary"], [class*="intro"],
    [class*="lead"], [class*="subtitle"] {
        display: none !important;
    }

    /* Hide post description/summary that comes from frontmatter */
    .post-summary, .article-summary,
    .post-excerpt, .article-excerpt,
    .entry-summary, .entry-excerpt,
    .content-summary, .page-description,
    .post-description, .article-description {
        display: none !important;
    }

    /* Hide header navigation and menu items */
    header nav, header .menu, header .navigation,
    .header-nav, .header-menu, .site-nav {
        display: none !important;
    }

    /* Remove any background colors or patterns */
    * {
        background: transparent !important;
        box-shadow: none !important;
    }

    /* Better spacing for lists */
    ul, ol {
        margin: 12px 0;
        padding-left: 24px;
    }

    li {
        margin-bottom: 6px;
        line-height: 1.6;
    }

    /* Strong and emphasis */
    strong, b {
        font-weight: bold !important;
    }

    em, i {
        font-style: italic !important;
    }

    /* Remove any fixed positioning or absolute positioning */
    * {
        position: static !important;
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
    }

    /* Prevent any element from exceeding column width */
    div, span, section, article, p, h1, h2, h3, h4, h5, h6 {
        max-width: 100% !important;
        box-sizing: border-box !important;
    }
    </style>
    """

    # Add the print CSS to the head
    head = soup.find('head')
    if head:
        head.append(BeautifulSoup(print_css, 'html.parser'))
    else:
        # If no head tag, create one
        head_tag = soup.new_tag('head')
        head_tag.append(BeautifulSoup(print_css, 'html.parser'))
        if soup.html:
            soup.html.insert(0, head_tag)
        else:
            soup.insert(0, head_tag)

    # Remove table of contents section
    # Look for elements containing "Section" or table of contents
    toc_elements = soup.find_all(['div', 'section', 'nav'],
                                 string=lambda text: text and ('Section' in text or 'Contents' in text))
    for elem in toc_elements:
        elem.decompose()

    # Remove any elements with class or id containing 'toc', 'contents', 'section'
    for selector in ['[class*="toc"]', '[id*="toc"]', '[class*="contents"]', '[id*="contents"]', '[class*="section"]']:
        for elem in soup.select(selector):
            elem.decompose()

    # Remove navigation elements
    # Remove nav elements and elements with nav-related classes
    nav_selectors = [
        'nav',
        '[class*="nav"]', '[id*="nav"]',
        '[class*="menu"]', '[id*="menu"]',
        'header nav', 'header ul', '.header-nav', '.site-nav'
    ]
    for selector in nav_selectors:
        for elem in soup.select(selector):
            elem.decompose()

    # Remove newsletter signup forms/boxes
    # Look for forms with action containing 'buttondown' or 'newsletter'
    signup_forms = soup.find_all('form', action=lambda x: x and ('buttondown' in x.lower() or 'newsletter' in x.lower()))
    for form in signup_forms:
        form.decompose()

    # Remove elements with newsletter-related classes or IDs
    newsletter_selectors = [
        '[class*="newsletter"]', '[id*="newsletter"]',
        '[class*="signup"]', '[id*="signup"]',
        '[class*="subscribe"]', '[id*="subscribe"]',
        '[class*="email"]', '[id*="email"]'
    ]
    for selector in newsletter_selectors:
        for elem in soup.select(selector):
            # Only remove if it contains signup-related text
            elem_text = elem.get_text().lower() if elem.get_text() else ''
            if any(keyword in elem_text for keyword in ['subscribe', 'newsletter', 'email', 'signup', 'join']):
                elem.decompose()

    # Look for divs/sections containing newsletter signup text
    signup_keywords = ['subscribe', 'newsletter signup', 'join our newsletter', 'get updates', 'email updates']
    for keyword in signup_keywords:
        signup_elements = soup.find_all(['div', 'section', 'form'],
                                       string=lambda text: text and keyword.lower() in text.lower())
        for elem in signup_elements:
            # Find the parent container that likely contains the whole signup box
            parent = elem.parent
            if parent and parent.name in ['div', 'section', 'aside']:
                parent.decompose()
            else:
                elem.decompose()

    # Remove redundant newsletter name and issue title from content area (since we have magazine header now)

    # Remove the post title div
    for elem in soup.find_all('div', class_='post-title'):
        elem.decompose()

    # Remove the single column header container
    for elem in soup.find_all('div', class_='single-column-header-container'):
        elem.decompose()

    # Remove any elements containing the issue title text
    if header_info['title']:
        for elem in soup.find_all(['h1', 'h2', 'h3', 'div']):
            if elem.get_text().strip() == header_info['title']:
                elem.decompose()

    # Remove "Previous Issues" section and everything after it
    # Look for heading containing "Previous Issues"
    prev_issues_heading = soup.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'],
                                    string=lambda text: text and 'Previous Issues' in text)

    if prev_issues_heading:
        # Remove everything from this heading onwards
        current = prev_issues_heading
        while current:
            next_sibling = current.next_sibling
            current.decompose()
            current = next_sibling

    # Also check for divs or sections containing "Previous Issues"
    prev_issues_sections = soup.find_all(['div', 'section'],
                                         string=lambda text: text and 'Previous Issues' in text)
    for section in prev_issues_sections:
        section.decompose()

    # Move copyright to page footer by hiding it from content (it's now in @bottom-left)
    for elem in soup.find_all(string=lambda text: text and 'Clayton Man' in text):
        if elem.parent:
            elem.parent['style'] = 'display: none;'

    # Create magazine-style header and wrap the main content
    body = soup.find('body')
    if body:
        # Create magazine header
        header_div = soup.new_tag('div', **{'class': 'magazine-header'})

        # Add background image if available
        if header_info['featured_image']:
            bg_img = soup.new_tag('img', **{
                'class': 'background-image',
                'src': header_info['featured_image'],
                'alt': 'Featured image'
            })
            header_div.append(bg_img)

        header_content = soup.new_tag('div', **{'class': 'header-content'})

        # Newsletter name
        newsletter_name = soup.new_tag('div', **{'class': 'newsletter-name'})
        newsletter_name.string = "The Sunday Blender"
        header_content.append(newsletter_name)

        # Issue title
        issue_title = soup.new_tag('div', **{'class': 'issue-title'})
        issue_title.string = header_info['title']
        header_content.append(issue_title)

        # Issue date - create a copy of title styling but smaller
        formatted_date = datetime.strptime(header_info['date'], '%Y-%m-%d').strftime('%b %d, %Y')
        issue_date = soup.new_tag('div', **{'class': 'issue-title', 'style': 'font-size: 18px !important; margin-top: 10px !important; opacity: 0.8 !important;'})
        issue_date.string = formatted_date
        header_content.append(issue_date)

        header_div.append(header_content)

        # Find the main content area (usually main, article, or the body contents)
        main_content = body.find(['main', 'article']) or body

        if main_content and main_content.name != 'body':
            # Insert header before main content and wrap main content
            main_content.insert_before(header_div)
            wrapper = soup.new_tag('div', **{'class': 'content-wrapper'})
            main_content.wrap(wrapper)
        else:
            # If no specific main content found, create structure
            # First add the header
            body.insert(0, header_div)

            # Then wrap remaining content
            wrapper = soup.new_tag('div', **{'class': 'content-wrapper'})
            body_contents = list(body.children)
            for child in body_contents:
                if child.name and child != header_div:  # Skip text nodes and header
                    child.extract()
                    wrapper.append(child)
            body.append(wrapper)

    # Create a temporary cleaned HTML file
    temp_html_path = html_path.parent / 'temp_cleaned.html'
    with open(temp_html_path, 'w', encoding='utf-8') as f:
        f.write(str(soup))

    return temp_html_path

def convert_html_to_pdf(html_path, output_path):
    """Convert HTML to PDF automatically using Chrome headless"""

    # Start progress indicator
    stop_event = threading.Event()
    progress_thread = threading.Thread(target=show_progress, args=("Converting HTML to PDF", stop_event))
    progress_thread.start()

    try:
        # Try Chrome headless first with print-optimized settings
        cmd = [
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            '--headless',
            '--disable-gpu',
            '--print-to-pdf=' + str(output_path),
            '--print-to-pdf-no-header',
            '--no-pdf-header-footer',
            '--disable-print-preview',
            '--hide-scrollbars',
            '--run-all-compositor-stages-before-draw',
            '--virtual-time-budget=15000',
            '--disable-background-timer-throttling',
            str(html_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0 and Path(output_path).exists():
            stop_event.set()
            progress_thread.join()
            print("\r", end="")  # Clear the progress indicator
            return True

    except FileNotFoundError:
        pass

    # Try Safari if Chrome doesn't work
    try:
        # Create a temporary AppleScript to use Safari
        applescript = f'''
        tell application "Safari"
            activate
            open location "file://{html_path}"
            delay 2
            tell application "System Events"
                key code 35 using command down -- Cmd+P
                delay 1
                click button "PDF" of sheet 1 of window 1 of application process "Safari"
                delay 1
                click menu item "Save as PDF..." of menu 1 of button "PDF" of sheet 1 of window 1 of application process "Safari"
                delay 1
                keystroke "{output_path}"
                key code 36 -- Enter
            end tell
        end tell
        '''

        with open('/tmp/safari_pdf.scpt', 'w') as f:
            f.write(applescript)

        result = subprocess.run(['osascript', '/tmp/safari_pdf.scpt'], capture_output=True)

        if result.returncode == 0:
            return True

    except:
        pass

    # Fallback to pandoc with default PDF engine
    try:
        cmd = [
            'pandoc',
            str(html_path),
            '-o', str(output_path),
            '--variable', 'geometry:margin=0.75in'
        ]

        result = subprocess.run(cmd, capture_output=True, text=True,
                              env={**os.environ, 'PATH': '/usr/local/texlive/2025basic/bin/universal-darwin:' + os.environ.get('PATH', '')})

        if result.returncode == 0:
            return True
        else:
            print(f"Pandoc error: {result.stderr}")

    except Exception as e:
        print(f"Pandoc failed: {e}")

    # Stop progress indicator on failure
    stop_event.set()
    progress_thread.join()
    print("\r❌ All automatic conversion methods failed.")
    return False

def main():
    """Main function"""
    if len(sys.argv) > 1:
        working_dir = sys.argv[1]
    else:
        working_dir = Path.cwd()

    try:
        print("🔍 Finding newsletter HTML file...")
        html_path = find_newsletter_html(working_dir)
        print(f"✅ Found HTML file: {html_path}")

        print("📝 Generating PDF filename...")
        pdf_name = get_pdf_name(working_dir)
        output_path = Path(working_dir) / pdf_name

        # If file exists, add counter to avoid overwriting
        if output_path.exists():
            base_name = output_path.stem  # filename without extension
            extension = output_path.suffix  # .pdf
            counter = 1

            while output_path.exists():
                new_name = f"{base_name}_{counter:02d}{extension}"
                output_path = Path(working_dir) / new_name
                counter += 1

            print(f"📄 Output: \033[96m{output_path.name}\033[0m (file exists, using counter)")
        else:
            print(f"📄 Output: \033[96m{pdf_name}\033[0m")

        print("✂️ Cleaning HTML content...")
        cleaned_html_path = clean_html_for_pdf(html_path, working_dir)

        # Convert to PDF
        try:
            if convert_html_to_pdf(cleaned_html_path, output_path):
                print(f"🎉 Success! PDF created: \033[96m{output_path.name}\033[0m")

                # Copy to static/pdf folder (always use original name, overwrite existing)
                original_pdf_name = pdf_name  # Use original name without counter
                static_pdf_path = Path("../../../../../static/pdf") / original_pdf_name
                static_pdf_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(output_path, static_pdf_path)

                public_url = f"/pdf/{original_pdf_name}"
                print(f"📂 Copied to static folder: \033[92mstatic/pdf/{original_pdf_name}\033[0m")
                print(f"🌐 Public URL: \033[94m{public_url}\033[0m")
                print(f"\n💡 Add this link to your newsletter:")
                print(f"   \033[93m[Download PDF]({public_url})\033[0m")

            else:
                print("❌ Failed to create PDF")
                sys.exit(1)
        finally:
            # Clean up temporary file
            if cleaned_html_path.exists():
                cleaned_html_path.unlink()

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()