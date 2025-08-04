#!/bin/bash

# Script to rename and resize image files for blog posts
# Requirements:
# 1. All filenames in small-caps
# 2. No spaces (replace with underscore)
# 3. Filename should not exceed 10 letters
# 4. Resize images to max width of 1200px while keeping aspect ratio

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to resize image if needed
resize_image() {
    local file="$1"
    local max_width=1200
    
    # Check if ImageMagick is available
    if ! command -v identify &> /dev/null; then
        echo -e "${YELLOW}Warning: ImageMagick not available, skipping resize for $file${NC}"
        return 0
    fi
    
    # Get current dimensions
    local dimensions=$(identify -format "%wx%h" "$file" 2>/dev/null)
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}Warning: Could not get dimensions for $file${NC}"
        return 0
    fi
    
    local width=$(echo "$dimensions" | cut -d'x' -f1)
    local height=$(echo "$dimensions" | cut -d'x' -f2)
    
    # Only resize if width is greater than max_width
    if [ "$width" -gt "$max_width" ]; then
        echo -e "${YELLOW}Resizing $file from ${width}x${height} to max width ${max_width}px${NC}"
        if convert "$file" -resize "${max_width}x" -quality 85 "$file"; then
            echo -e "${GREEN}✓${NC} Successfully resized $file"
            return 0
        else
            echo -e "${RED}✗${NC} Failed to resize $file"
            return 1
        fi
    else
        echo -e "${GREEN}✓${NC} $file (width ${width}px, no resize needed)"
        return 0
    fi
}

# Function to process a single file
process_file() {
    local file="$1"
    local dir="$(dirname "$file")"
    local filename="$(basename "$file")"
    local extension="${filename##*.}"
    local name_without_ext="${filename%.*}"
    
    # Convert to lowercase
    local lowercase_name=$(echo "$name_without_ext" | tr '[:upper:]' '[:lower:]')
    
    # Replace spaces with underscores
    local no_spaces=$(echo "$lowercase_name" | sed 's/ /_/g')
    
    # Remove any other special characters except underscores and hyphens
    local clean_name=$(echo "$no_spaces" | sed 's/[^a-z0-9_-]//g')
    
    # Truncate to 10 characters if longer
    local truncated_name="${clean_name:0:10}"
    
    # Remove trailing underscores or hyphens
    truncated_name=$(echo "$truncated_name" | sed 's/[_\-]*$//')
    
    # Ensure we have at least 1 character
    if [ -z "$truncated_name" ]; then
        truncated_name="img"
    fi
    
    # Create new filename
    local new_filename="${truncated_name}.${extension}"
    local new_path="${dir}/${new_filename}"
    
    # Check if the new filename would be the same
    if [ "$filename" = "$new_filename" ]; then
        echo -e "${GREEN}✓${NC} $filename (no change needed)"
        # Still resize if needed
        resize_image "$file"
        return 0
    fi
    
    # Handle duplicate filenames by adding a number
    local counter=1
    local original_new_filename="$new_filename"
    while [ -f "$new_path" ]; do
        local name_without_ext="${original_new_filename%.*}"
        local ext="${original_new_filename##*.}"
        new_filename="${name_without_ext}${counter}.${ext}"
        new_path="${dir}/${new_filename}"
        counter=$((counter + 1))
        
        # Prevent infinite loop
        if [ $counter -gt 10 ]; then
            echo -e "${RED}✗${NC} Cannot rename $filename (too many duplicates)"
            return 1
        fi
    done
    
    # First resize the image if needed
    resize_image "$file"
    
    # Then rename the file
    if mv "$file" "$new_path"; then
        echo -e "${GREEN}✓${NC} $filename → $new_filename"
        return 0
    else
        echo -e "${RED}✗${NC} Failed to rename $filename"
        return 1
    fi
}

# Function to capture file information for summary
capture_file_info() {
    local file="$1"
    local filename="$(basename "$file")"
    local size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null)
    local dimensions=""
    
    if command -v identify &> /dev/null; then
        dimensions=$(identify -format "%wx%h" "$file" 2>/dev/null || echo "unknown")
    else
        dimensions="unknown"
    fi
    
    echo "$filename|$size|$dimensions"
}

# Function to find and process all image files
find_and_process_images() {
    local search_dir="$1"
    local supported_extensions="jpg jpeg png webp avif gif svg"
    local total_files=0
    local processed_files=0
    local failed_files=0
    local renamed_files=0
    local resized_files=0
    
    # Arrays to store before/after information
    declare -a before_files
    declare -a after_files
    
    echo -e "${YELLOW}Searching for image files in: $search_dir${NC}"
    echo "Supported extensions: $supported_extensions"
    echo "----------------------------------------"
    
    # First pass: capture original state
    echo "Capturing original file information..."
    while IFS= read -r -d '' file; do
        before_files+=("$(capture_file_info "$file")")
    done < <(find "$search_dir" -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.webp" -o -iname "*.avif" -o -iname "*.gif" -o -iname "*.svg" \) -print0)
    
    # Second pass: process files
    while IFS= read -r -d '' file; do
        total_files=$((total_files + 1))
        local original_filename="$(basename "$file")"
        local original_size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null)
        local original_dimensions=""
        
        if command -v identify &> /dev/null; then
            original_dimensions=$(identify -format "%wx%h" "$file" 2>/dev/null || echo "unknown")
        fi
        
        if process_file "$file"; then
            processed_files=$((processed_files + 1))
            
            # Check if file was renamed
            local new_filename="$(basename "$file")"
            if [ "$original_filename" != "$new_filename" ]; then
                renamed_files=$((renamed_files + 1))
            fi
            
            # Check if file was resized
            local new_size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null)
            if [ "$original_size" != "$new_size" ]; then
                resized_files=$((resized_files + 1))
            fi
        else
            failed_files=$((failed_files + 1))
        fi
    done < <(find "$search_dir" -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.webp" -o -iname "*.avif" -o -iname "*.gif" -o -iname "*.svg" \) -print0)
    
    # Third pass: capture final state
    echo "Capturing final file information..."
    while IFS= read -r -d '' file; do
        after_files+=("$(capture_file_info "$file")")
    done < <(find "$search_dir" -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.webp" -o -iname "*.avif" -o -iname "*.gif" -o -iname "*.svg" \) -print0)
    
    # Display summary
    display_summary "$search_dir" "$total_files" "$processed_files" "$failed_files" "$renamed_files" "$resized_files" "${before_files[@]}" "${after_files[@]}"
}

# Function to display comprehensive summary
display_summary() {
    local search_dir="$1"
    local total_files="$2"
    local processed_files="$3"
    local failed_files="$4"
    local renamed_files="$5"
    local resized_files="$6"
    shift 6
    local before_files=("$@")
    local after_files=()
    
    # Separate before and after arrays
    local array_size=${#before_files[@]}
    local half_size=$((array_size / 2))
    
    for ((i=0; i<half_size; i++)); do
        after_files+=("${before_files[$((i + half_size))]}")
    done
    
    for ((i=0; i<half_size; i++)); do
        before_files[$((i + half_size))]=""
    done
    
    # Calculate total sizes
    local total_before_size=0
    local total_after_size=0
    
    for info in "${before_files[@]}"; do
        if [ -n "$info" ]; then
            local size=$(echo "$info" | cut -d'|' -f2)
            total_before_size=$((total_before_size + size))
        fi
    done
    
    for info in "${after_files[@]}"; do
        if [ -n "$info" ]; then
            local size=$(echo "$info" | cut -d'|' -f2)
            total_after_size=$((total_after_size + size))
        fi
    done
    
    # Calculate savings
    local size_savings=$((total_before_size - total_after_size))
    local savings_percentage=0
    if [ $total_before_size -gt 0 ]; then
        savings_percentage=$((size_savings * 100 / total_before_size))
    fi
    
    # Format sizes for display
    local before_size_formatted=$(numfmt --to=iec-i --suffix=B "$total_before_size" 2>/dev/null || echo "${total_before_size}B")
    local after_size_formatted=$(numfmt --to=iec-i --suffix=B "$total_after_size" 2>/dev/null || echo "${total_after_size}B")
    local savings_formatted=$(numfmt --to=iec-i --suffix=B "$size_savings" 2>/dev/null || echo "${size_savings}B")
    
    echo ""
    echo "========================================"
    echo -e "${YELLOW}📊 PROCESSING SUMMARY${NC}"
    echo "========================================"
    echo "Directory: $search_dir"
    echo "Total files found: $total_files"
    echo -e "${GREEN}Successfully processed: $processed_files${NC}"
    echo -e "${YELLOW}Files renamed: $renamed_files${NC}"
    echo -e "${YELLOW}Files resized: $resized_files${NC}"
    if [ $failed_files -gt 0 ]; then
        echo -e "${RED}Failed: $failed_files${NC}"
    fi
    
    echo ""
    echo "========================================"
    echo -e "${YELLOW}💾 TOTAL SIZE COMPARISON${NC}"
    echo "========================================"
    echo -e "Total size before: ${YELLOW}$before_size_formatted${NC}"
    echo -e "Total size after:  ${GREEN}$after_size_formatted${NC}"
    if [ $size_savings -gt 0 ]; then
        echo -e "Size savings:      ${GREEN}$savings_formatted (${savings_percentage}%)${NC}"
    elif [ $size_savings -lt 0 ]; then
        echo -e "Size increase:     ${RED}${savings_formatted#-} (${savings_percentage}%)${NC}"
    else
        echo -e "Size change:       ${GREEN}No change${NC}"
    fi
    
    echo ""
    echo "========================================"
    echo -e "${YELLOW}📁 BEFORE & AFTER COMPARISON${NC}"
    echo "========================================"
    
    # Create a temporary file to store current state
    local temp_file=$(mktemp)
    find "$search_dir" -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.webp" -o -iname "*.avif" -o -iname "*.gif" -o -iname "*.svg" \) -exec basename {} \; | sort > "$temp_file"
    
    # Display comparison table
    printf "%-25s %-15s %-15s %-15s %-15s\n" "Filename" "Size (Before)" "Size (After)" "Dimensions" "Status"
    printf "%-25s %-15s %-15s %-15s %-15s\n" "--------" "------------" "-----------" "-----------" "------"
    
    while IFS= read -r filename; do
        # Find before info
        local before_info=""
        for info in "${before_files[@]}"; do
            if [[ "$info" == "$filename|"* ]]; then
                before_info="$info"
                break
            fi
        done
        
        # Find after info
        local after_info=""
        for info in "${after_files[@]}"; do
            if [[ "$info" == "$filename|"* ]]; then
                after_info="$info"
                break
            fi
        done
        
        if [ -n "$before_info" ] && [ -n "$after_info" ]; then
            local before_size=$(echo "$before_info" | cut -d'|' -f2)
            local after_size=$(echo "$after_info" | cut -d'|' -f2)
            local dimensions=$(echo "$after_info" | cut -d'|' -f3)
            
            # Format file sizes
            local before_size_formatted=$(numfmt --to=iec-i --suffix=B "$before_size" 2>/dev/null || echo "${before_size}B")
            local after_size_formatted=$(numfmt --to=iec-i --suffix=B "$after_size" 2>/dev/null || echo "${after_size}B")
            
            # Determine status
            local status=""
            local status_color=""
            if [ "$before_size" != "$after_size" ]; then
                status="RESIZED"
                status_color="${YELLOW}"
            else
                status="OK"
                status_color="${GREEN}"
            fi
            
            printf "%-25s %-15s %-15s %-15s " "$filename" "$before_size_formatted" "$after_size_formatted" "$dimensions"
            echo -e "${status_color}${status}${NC}"
        fi
    done < "$temp_file"
    
    # Clean up
    rm "$temp_file"
    
    echo ""
    echo "========================================"
    echo -e "${GREEN}✅ PROCESSING COMPLETE${NC}"
    echo "========================================"
}

# Main script
main() {
    local target_dir="${1:-content/posts}"
    
    # Check if target directory exists
    if [ ! -d "$target_dir" ]; then
        echo -e "${RED}Error: Directory '$target_dir' does not exist${NC}"
        echo "Usage: $0 [directory]"
        echo "Default directory: content/posts"
        exit 1
    fi
    
    # Check if ImageMagick is available (optional check)
    if ! command -v identify &> /dev/null; then
        echo -e "${YELLOW}Warning: ImageMagick not found. This script only renames files.${NC}"
        echo "To install ImageMagick: brew install imagemagick (macOS) or apt-get install imagemagick (Ubuntu)"
    fi
    
    echo -e "${YELLOW}Image File Renaming and Resizing Script${NC}"
    echo "This script will:"
    echo "1. Convert filenames to lowercase"
    echo "2. Replace spaces with underscores"
    echo "3. Remove special characters"
    echo "4. Truncate to 10 characters maximum"
    echo "5. Resize images to max width of 1200px (maintaining aspect ratio)"
    echo ""
    
    read -p "Do you want to proceed? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Operation cancelled."
        exit 0
    fi
    
    find_and_process_images "$target_dir"
}

# Run main function with arguments
main "$@" 