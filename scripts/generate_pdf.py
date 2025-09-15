#!/usr/bin/env python3
"""
PDF Generation Script for Sunday Blender Newsletter
Converts index.md to PDF, removing front matter and converting WebP images.
Run from the post directory containing index.md
"""

import os
import sys
import re
from pathlib import Path
import subprocess
import shutil
from PIL import Image

def remove_frontmatter(content):
    """Remove YAML front matter from markdown content"""
    # Match front matter between --- delimiters
    pattern = r'^---\n.*?\n---\n'
    return re.sub(pattern, '', content, flags=re.DOTALL | re.MULTILINE)

def remove_unicode_characters(content):
    """Remove non-ASCII Unicode characters that cause LaTeX issues"""
    # Replace common Unicode characters with ASCII equivalents or remove them
    unicode_replacements = {
        '"': '"',  # Left double quotation mark
        '"': '"',  # Right double quotation mark
        ''': "'",  # Left single quotation mark
        ''': "'",  # Right single quotation mark
        '—': '--',  # Em dash
        '–': '-',   # En dash
        '…': '...',  # Horizontal ellipsis
    }

    # Apply replacements
    for unicode_char, ascii_replacement in unicode_replacements.items():
        content = content.replace(unicode_char, ascii_replacement)

    # Remove any remaining non-ASCII characters
    content = ''.join(char if ord(char) < 128 else '' for char in content)

    return content

def remove_figure_captions(content):
    """Remove figure captions that appear as 'Figure X: Title' patterns"""
    # Remove lines that start with "Figure" followed by number and colon
    pattern = r'^Figure \d+:.*$'
    content = re.sub(pattern, '', content, flags=re.MULTILINE)

    # Clean up any resulting empty lines
    content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)

    return content

def convert_webp_images(content, working_dir):
    """Convert WebP images to PNG and update markdown references, detecting by content not extension"""
    working_path = Path(working_dir).resolve()

    # Find all image references in markdown
    image_pattern = r'!\[(.*?)\]\((.*?\.(webp|png|jpg|jpeg|gif))\)'
    images = re.findall(image_pattern, content, re.IGNORECASE)

    updated_content = content

    for alt_text, image_path, ext in images:
        image_file = working_path / image_path

        # Skip if image doesn't exist
        if not image_file.exists():
            print(f"Warning: Image not found: {image_file}")
            continue

        # Detect actual file type by content, not extension
        try:
            with Image.open(image_file) as img:
                actual_format = img.format.lower()

            # Convert WebP (or misnamed WebP files) to PNG
            if actual_format == 'webp' or ext.lower() == 'webp':
                png_path = image_file.with_suffix('.png')

                try:
                    # Convert using PIL
                    with Image.open(image_file) as img:
                        # Convert to RGB if necessary (WebP can be RGBA)
                        if img.mode in ('RGBA', 'LA', 'P'):
                            img = img.convert('RGB')
                        img.save(png_path, 'PNG')

                    # Update content to reference PNG with empty alt text (no caption)
                    old_ref = f'![{alt_text}]({image_path})'
                    new_ref = f'![]({png_path.name})'
                    updated_content = updated_content.replace(old_ref, new_ref)

                    print(f"Converted: {image_file.name} -> {png_path.name} (was {actual_format})")

                except Exception as e:
                    print(f"Error converting {image_file}: {e}")
                    # Remove the image reference if conversion fails
                    old_ref = f'![{alt_text}]({image_path})'
                    updated_content = updated_content.replace(old_ref, '')
            else:
                # For other formats, keep as is
                pass

        except Exception as e:
            print(f"Warning: Could not read image {image_file}: {e}")
            # Try to convert anyway in case it's a corrupted but recoverable file
            try:
                png_path = image_file.with_suffix('.png')
                with Image.open(image_file) as img:
                    if img.mode in ('RGBA', 'LA', 'P'):
                        img = img.convert('RGB')
                    img.save(png_path, 'PNG')

                old_ref = f'![{alt_text}]({image_path})'
                new_ref = f'![]({png_path.name})'
                updated_content = updated_content.replace(old_ref, new_ref)
                print(f"Recovered and converted: {image_file.name} -> {png_path.name}")
            except:
                # Remove the image reference if all else fails
                old_ref = f'![{alt_text}]({image_path})'
                updated_content = updated_content.replace(old_ref, '')
                print(f"Removed problematic image: {image_file.name}")

    return updated_content

def get_post_title_from_frontmatter(content):
    """Extract title from front matter for PDF filename"""
    frontmatter_match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
    if frontmatter_match:
        frontmatter = frontmatter_match.group(1)
        title_match = re.search(r'^title:\s*["\']?(.*?)["\']?\s*$', frontmatter, re.MULTILINE)
        if title_match:
            return title_match.group(1).strip()
    return "Sunday Blender Newsletter"

def convert_to_pdf(markdown_file, output_dir=None):
    """Convert markdown to PDF using pandoc"""
    if not Path(markdown_file).exists():
        raise FileNotFoundError(f"Markdown file not found: {markdown_file}")

    # Read the markdown content
    with open(markdown_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Get title and date for filename
    title = get_post_title_from_frontmatter(content)
    date_match = re.search(r'^date:\s*(.*?)\s*$', content, re.MULTILINE)
    date = date_match.group(1).strip() if date_match else ""

    # Remove front matter, Unicode characters, figure captions, and convert WebP images
    clean_content = remove_frontmatter(content)
    clean_content = remove_unicode_characters(clean_content)
    clean_content = remove_figure_captions(clean_content)
    clean_content = convert_webp_images(clean_content, Path(markdown_file).parent)

    # Create temporary markdown file without front matter
    temp_md = Path(markdown_file).parent / "temp_clean.md"
    with open(temp_md, 'w', encoding='utf-8') as f:
        f.write(clean_content)

    # Create PDF filename: The-Sunday-Blender-YYYY-MM-DD-Title.pdf
    clean_title = title.replace(' ', '-').replace('"', '').replace("'", "")
    pdf_filename = f"The-Sunday-Blender-{date}-{clean_title}.pdf"

    # Determine output path
    if output_dir:
        output_path = Path(output_dir) / pdf_filename
    else:
        output_path = Path(markdown_file).parent / pdf_filename

    try:
        # Use pandoc to convert to PDF - run from the working directory
        cmd = [
            'pandoc',
            temp_md.name,
            '-o', output_path.name,
            '--variable', 'geometry:margin=1in',
            '--variable', 'fontsize=11pt',
            '--toc',
            '--toc-depth=2'
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(markdown_file).parent)

        if result.returncode != 0:
            print(f"Error converting to PDF: {result.stderr}")
            return None

        print(f"PDF generated successfully: {output_path}")
        return output_path

    finally:
        # Clean up temporary file
        if temp_md.exists():
            temp_md.unlink()

def main():
    """Main function to generate PDF from current directory's index.md"""
    current_dir = Path.cwd()
    markdown_file = current_dir / "index.md"

    if not markdown_file.exists():
        print("Error: index.md not found in current directory")
        print(f"Current directory: {current_dir}")
        sys.exit(1)

    try:
        pdf_path = convert_to_pdf(markdown_file)
        if pdf_path:
            print(f"Success! PDF created: {pdf_path}")
        else:
            print("Failed to generate PDF")
            sys.exit(1)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()