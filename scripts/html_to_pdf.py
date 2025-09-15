#!/usr/bin/env python3
"""
HTML to PDF Converter for Sunday Blender Newsletter
Converts the built Hugo HTML page to PDF
"""

import os
import sys
import re
import subprocess
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

    slug = slug_match.group(1).strip()

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
    clean_title = title.replace(' ', '-').replace('"', '').replace("'", "")
    clean_title = re.sub(r'[<>:"/\\|?*]', '', clean_title)

    return f"The-Sunday-Blender-{date}-{clean_title}.pdf"

def clean_html_for_pdf(html_path):
    """Remove unwanted sections and optimize HTML for A4 print PDF"""
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, 'html.parser')

    # Add print-friendly CSS styles
    print_css = """
    <style type="text/css" media="print">
    @page {
        size: A4;
        margin: 0.75in;
    }

    body {
        font-family: 'Times New Roman', serif;
        font-size: 14px !important;
        line-height: 1.6 !important;
        color: #000 !important;
        background: white !important;
        column-count: 2;
        column-gap: 0.5in;
        column-rule: 1px solid #ddd;
        text-align: justify;
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
        font-size: 18px !important;
        margin: 16px 0 10px 0 !important;
        font-weight: bold !important;
        break-after: avoid;
    }

    h3 {
        font-size: 16px !important;
        margin: 12px 0 8px 0 !important;
        font-weight: bold !important;
    }

    p {
        font-size: 14px !important;
        line-height: 1.6 !important;
        margin-bottom: 12px !important;
        text-indent: 16px;
        orphans: 2;
        widows: 2;
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
            print(f"\r✅ PDF created successfully using Chrome: {output_path}")
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
            print(f"PDF created using Safari: {output_path}")
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
            print(f"PDF created using pandoc: {output_path}")
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
        print(f"📄 Output: {pdf_name}")

        print("✂️ Cleaning HTML content...")
        cleaned_html_path = clean_html_for_pdf(html_path)
        print("✅ Removed table of contents and Previous Issues section")

        # Convert to PDF
        try:
            if convert_html_to_pdf(cleaned_html_path, output_path):
                print(f"🎉 Success! PDF created: {output_path}")
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