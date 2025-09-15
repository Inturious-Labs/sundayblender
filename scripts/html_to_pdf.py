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

def convert_html_to_pdf(html_path, output_path):
    """Convert HTML to PDF automatically using Chrome headless"""

    # Start progress indicator
    stop_event = threading.Event()
    progress_thread = threading.Thread(target=show_progress, args=("Converting HTML to PDF", stop_event))
    progress_thread.start()

    try:
        # Try Chrome headless first
        cmd = [
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            '--headless',
            '--disable-gpu',
            '--print-to-pdf=' + str(output_path),
            '--no-margins',
            '--print-to-pdf-no-header',
            '--disable-print-preview',
            '--hide-scrollbars',
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

        # Convert to PDF
        if convert_html_to_pdf(html_path, output_path):
            print(f"🎉 Success! PDF created: {output_path}")
        else:
            print("❌ Failed to create PDF")
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()