#!/bin/bash

# fetch_image.sh — Fetch an image from a Google Images link, then normalize it
# for use in TSB blog posts.
#
# Workflow:
#   1. Copy the image address from Google Images (right-click the LARGE
#      preview image → "Copy image address" — NOT the search-result link).
#   2. Script resolves it to the real, full-resolution source image URL.
#   3. Downloads it into the issue folder (or ~/Downloads/).
#   4. Reformats to JPEG, capped at 1200px wide and <= 500KB.
#
# Usage:
#   tsb-fetch-image "<image-url>" [output-name]              # -> ~/Downloads/
#   tsb-fetch-image --issue 0517 "<image-url>" [name]        # -> that issue
#   cd content/posts/2026/0517 && tsb-fetch-image "<url>"    # -> current folder
#
# Flags:
#   --issue YYYYMMDD   Save into content/posts/<YYYY>/<MMDD>/ instead of
#                      ~/Downloads/. If you run the script from inside an
#                      issue folder, that folder is used automatically.
#
# Notes:
#   - Primary input is "Copy image address" on the full-size image. A bare
#     gstatic.com THUMBNAIL link does not contain the full image and cannot
#     be rescued — the script detects this and tells you to re-copy.
#   - Companion to image_process.sh (which batch-processes already-downloaded
#     files in a directory). This one does the fetch + single-file normalize.

set -euo pipefail

# Colors for output (match image_process.sh conventions)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

MAX_WIDTH=1200
MAX_BYTES=512000          # 500 KB
PRIMARY_QUALITY=82        # fixed-quality first pass (user-chosen)
FALLBACK_QUALITY=70       # single safety-net re-encode if still over budget
UA="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

# Repo root, so --issue resolves regardless of where the script runs from.
# (Script lives in <repo>/scripts/, so root is its parent's parent.)
# NOTE: this script is invoked via a symlink (/usr/local/bin/tsb-fetch-image),
# and BASH_SOURCE is the SYMLINK path, not its target. Resolve the real path
# first — otherwise SCRIPT_DIR becomes /usr/local/bin and the repo isn't found.
# macOS Bash has no `readlink -f`; Python's realpath is reliable everywhere.
REAL_SOURCE="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "${BASH_SOURCE[0]}" 2>/dev/null \
    || readlink -f "${BASH_SOURCE[0]}" 2>/dev/null \
    || printf '%s' "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(cd "$(dirname "$REAL_SOURCE")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

die() {
    echo -e "${RED}✗ $1${NC}" >&2
    exit 1
}

# --- argument handling ------------------------------------------------------

usage() {
    echo "Usage: $0 [--issue YYYYMMDD] \"<image-url>\" [output-name]"
    echo
    echo "Primary input: in Google Images, click the result to open the large"
    echo "preview, then right-click the BIG image and choose 'Copy image"
    echo "address'. Paste that URL here."
    echo
    echo "  --issue YYYYMMDD   Save into content/posts/YYYY/MMDD/ instead of"
    echo "                     ~/Downloads/. (Auto-detected if you run this"
    echo "                     from inside an issue folder.)"
    exit 1
}

ISSUE=""
POSITIONAL=()
while [ $# -gt 0 ]; do
    case "$1" in
        --issue)
            [ $# -ge 2 ] || die "--issue requires a YYYYMMDD value."
            ISSUE="$2"
            shift 2
            ;;
        --issue=*)
            ISSUE="${1#*=}"
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            POSITIONAL+=("$1")
            shift
            ;;
    esac
done

[ "${#POSITIONAL[@]}" -ge 1 ] || usage
INPUT_URL="${POSITIONAL[0]}"
OUTPUT_NAME="${POSITIONAL[1]:-}"

command -v magick &> /dev/null || die "ImageMagick (magick) not found. Install: brew install imagemagick"
command -v curl   &> /dev/null || die "curl not found."

# --- resolve destination directory -----------------------------------------
# Priority: explicit --issue  >  current dir if it's an issue folder  >  ~/Downloads

resolve_issue_dir() {
    local issue="$1"
    # Accept YYYYMMDD (8 digits) or MMDD (4 digits, current year assumed).
    local year mmdd
    if [[ "$issue" =~ ^[0-9]{8}$ ]]; then
        year="${issue:0:4}"
        mmdd="${issue:4:4}"
    elif [[ "$issue" =~ ^[0-9]{4}$ ]]; then
        year="$(date +%Y)"
        mmdd="$issue"
    else
        die "--issue must be YYYYMMDD or MMDD (got '$issue')."
    fi
    printf '%s/content/posts/%s/%s' "$REPO_ROOT" "$year" "$mmdd"
}

if [ -n "$ISSUE" ]; then
    DOWNLOAD_DIR="$(resolve_issue_dir "$ISSUE")"
    [ -d "$DOWNLOAD_DIR" ] || die "Issue folder does not exist: $DOWNLOAD_DIR
   Create the issue first (tsb-init-article), or check the date."
elif [[ "$(pwd)" == "${REPO_ROOT}/content/posts/"*/* ]]; then
    # Running from inside an issue folder — mirror tsb-init-article behavior.
    DOWNLOAD_DIR="$(pwd)"
else
    DOWNLOAD_DIR="${HOME}/Downloads"
fi

# --- URL-decode helper ------------------------------------------------------

urldecode() {
    # Decode %XX escapes and '+' -> space. Pure bash + printf.
    local data="${1//+/ }"
    printf '%b' "${data//%/\\x}"
}

# --- step 1: resolve to the real source image URL ---------------------------

resolve_source_url() {
    local url="$1"

    case "$url" in
        *gstatic.com*|*google.com/*tbn:*)
            # Thumbnail cache — not the full image, and unrecoverable.
            die "That link is a Google THUMBNAIL (gstatic.com), not the full image.
   It does not contain full-resolution data.
   Fix: in Google Images, click the result to open the large preview,
   then right-click the big image → 'Copy image address', and rerun
   this script with that URL."
            ;;
    esac

    # google.com/imgres?...&imgurl=ENCODED... or google.com/url?...&url=ENCODED...
    if [[ "$url" == *"google."*"/imgres?"* ]] || [[ "$url" == *"google."*"/url?"* ]]; then
        local extracted=""
        # Try imgurl= first (image search), then url= (generic redirect).
        extracted="$(printf '%s' "$url" | sed -n 's/.*[?&]imgurl=\([^&]*\).*/\1/p')"
        if [ -z "$extracted" ]; then
            extracted="$(printf '%s' "$url" | sed -n 's/.*[?&]url=\([^&]*\).*/\1/p')"
        fi
        [ -n "$extracted" ] || die "Could not extract a source image URL from that Google link.
   Try 'Copy image address' on the full-size image instead."
        urldecode "$extracted"
        return
    fi

    # Already a direct URL — pass through.
    printf '%s' "$url"
}

echo -e "${YELLOW}Resolving source URL...${NC}"
SOURCE_URL="$(resolve_source_url "$INPUT_URL")"
echo -e "  → ${SOURCE_URL}"

# Derive a referer (scheme://host) — many CDNs 403 a request with no referer.
REFERER="$(printf '%s' "$SOURCE_URL" | sed -n 's,^\(https\?://[^/]*\).*,\1/,p')"

# --- step 2: download into the destination directory ------------------------

mkdir -p "$DOWNLOAD_DIR"
RAW_TMP="$(mktemp "${DOWNLOAD_DIR}/.tsb_fetch_XXXXXX")"
trap 'rm -f "$RAW_TMP"' EXIT

echo -e "${YELLOW}Downloading...${NC}"
http_code="$(curl -sS -L \
    -A "$UA" \
    ${REFERER:+--referer "$REFERER"} \
    --max-time 60 \
    -w '%{http_code}' \
    -o "$RAW_TMP" \
    "$SOURCE_URL" || true)"

[ "$http_code" = "200" ] || die "Download failed (HTTP ${http_code:-?}).
   The source site may block hotlinking. Open the image in a browser,
   save it manually, then run image_process.sh on it instead."

[ -s "$RAW_TMP" ] || die "Downloaded file is empty."

# Validate it is actually an image, not an HTML error/captcha page.
MIME="$(file -b --mime-type "$RAW_TMP")"
case "$MIME" in
    image/*) : ;;
    *) die "Downloaded content is '$MIME', not an image.
   The link likely points to a web page, not a raw image file.
   Use 'Copy image address' on the actual image and retry." ;;
esac
echo -e "  ${GREEN}✓${NC} got ${MIME} ($(du -h "$RAW_TMP" | cut -f1))"

# --- step 3: pick output filename -------------------------------------------

# Sanitize a candidate into a blog-image slug: lowercase, alnum + _ -,
# max 10 chars, no trailing separators (matches image_process.sh rules).
slugify() {
    local s
    s="$(printf '%s' "$1" \
        | tr '[:upper:]' '[:lower:]' \
        | tr ' ' '_' \
        | sed 's/[^a-z0-9_-]//g')"
    s="${s:0:10}"
    s="$(printf '%s' "$s" | sed 's/[_-]*$//')"
    printf '%s' "$s"
}

if [ -n "$OUTPUT_NAME" ]; then
    # Explicit name given — use it, no prompt (fast path).
    slug="$(slugify "${OUTPUT_NAME%.*}")"
    [ -n "$slug" ] || die "Output name '$OUTPUT_NAME' is empty after sanitizing."
else
    # Default suggestion from the URL basename (often junk like 'aa238wry').
    base="$(basename "${SOURCE_URL%%\?*}")"
    default_slug="$(slugify "${base%.*}")"
    [ -n "$default_slug" ] || default_slug="img"

    if [ -t 0 ]; then
        # Interactive: require a deliberate name; pre-fill the URL default.
        echo -e "${YELLOW}Name this image${NC} (lowercase, ≤10 chars; Enter = '${default_slug}'):"
        read -r -p "  name: " typed_name || typed_name=""
        if [ -n "$typed_name" ]; then
            slug="$(slugify "$typed_name")"
            [ -n "$slug" ] || { echo -e "  ${YELLOW}(unusable, using '${default_slug}')${NC}"; slug="$default_slug"; }
        else
            slug="$default_slug"
        fi
    else
        # Non-interactive (piped/cron): can't prompt — use the URL default.
        slug="$default_slug"
    fi
fi

OUT="${DOWNLOAD_DIR}/${slug}.jpg"
# Avoid clobbering an existing file.
counter=1
while [ -e "$OUT" ]; do
    OUT="${DOWNLOAD_DIR}/${slug}${counter}.jpg"
    counter=$((counter + 1))
    [ "$counter" -gt 50 ] && die "Too many existing files named like ${slug}*.jpg"
done

# --- step 4: reformat -> jpeg, <=1200px wide, <=500KB -----------------------

echo -e "${YELLOW}Reformatting...${NC}"

# -resize "1200x>": shrink only if wider than 1200; never upscale (the '>').
# -flatten + white bg: handle transparent PNG/WebP so JPEG isn't black.
# -strip: drop metadata to save bytes.
magick "$RAW_TMP" \
    -background white -flatten \
    -resize "${MAX_WIDTH}x>" \
    -strip \
    -quality "$PRIMARY_QUALITY" \
    "$OUT" || die "ImageMagick failed to convert the image."

bytes="$(stat -f%z "$OUT" 2>/dev/null || stat -c%s "$OUT")"

if [ "$bytes" -gt "$MAX_BYTES" ]; then
    echo -e "  ${YELLOW}$(numfmt --to=iec-i --suffix=B "$bytes" 2>/dev/null || echo "${bytes}B") > 500KiB at q${PRIMARY_QUALITY}; re-encoding once at q${FALLBACK_QUALITY}...${NC}"
    magick "$OUT" -strip -quality "$FALLBACK_QUALITY" "$OUT" \
        || die "Fallback re-encode failed."
    bytes="$(stat -f%z "$OUT" 2>/dev/null || stat -c%s "$OUT")"
fi

dims="$(magick identify -format '%wx%h' "$OUT")"
size_fmt="$(numfmt --to=iec-i --suffix=B "$bytes" 2>/dev/null || echo "${bytes}B")"

echo
echo "========================================"
echo -e "${GREEN}✅ DONE${NC}"
echo "========================================"
echo -e "File:       ${GREEN}${OUT}${NC}"
echo -e "Dimensions: ${dims}"
echo -e "Size:       ${size_fmt}"
if [ "$bytes" -gt "$MAX_BYTES" ]; then
    echo -e "${YELLOW}Note: still above 500KB even at q${FALLBACK_QUALITY}. The source is very"
    echo -e "      detailed; consider a narrower crop or lower target width.${NC}"
fi
