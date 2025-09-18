#!/bin/bash

# PDF Generation Script for Sunday Blender Newsletter
# Usage: Run this script from any newsletter directory containing index.md

# Get the directory where this script is actually located (scripts folder)
# Follow symlinks to find the real script location
REAL_SCRIPT="$(readlink -f "${BASH_SOURCE[0]}" 2>/dev/null || realpath "${BASH_SOURCE[0]}" 2>/dev/null || echo "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(cd "$(dirname "$REAL_SCRIPT")" && pwd)"

# Run the PDF generation script with the current directory as argument
python3 "$SCRIPT_DIR/html_to_pdf.py" "$(pwd)"