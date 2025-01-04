#!/bin/bash

# Set the source directory containing .mp4 files
source_dir="/Volumes/Multimedia/Videos/Kids/Lucy/mp4/merged"
output_dir="$source_dir" # Output merged file in the same folder

# Check if the source directory exists and contains .mp4 files
if [ ! -d "$source_dir" ] || [ -z "$(ls "$source_dir"/*.mp4 2>/dev/null)" ]; then
  echo "No .mp4 files found in the source directory: $source_dir"
  exit 1
fi

# Temporary files and directories
file_list="$output_dir/mp4_file_list.txt"
temp_dir="$output_dir/temp"
mkdir -p "$temp_dir"

# Function to determine the transpose value based on EXIF rotation metadata
get_transpose_value() {
  local file="$1"
  local rotation=$(ffprobe -v error -select_streams v:0 -show_entries stream_tags=rotate -of default=noprint_wrappers=1:nokey=1 "$file")
  case "$rotation" in
    90) echo "1" ;;  # 90 degrees clockwise
    180) echo "2" ;; # 180 degrees
    270) echo "3" ;; # 90 degrees counter-clockwise
    *) echo "0" ;;   # No rotation needed
  esac
}

# Sort files numerically by name and then by creation time
sorted_files=($(ls "$source_dir"/*.mp4 | sort -t '/' -k2,2n || ls -1 "$source_dir"/*.mp4 | xargs stat -c '%W %n' | sort -n | cut -d ' ' -f2-))

# Get the name of the first file for the output prefix
first_file=$(basename "${sorted_files[0]}" .mp4)
output_prefix="$first_file"

# Normalize orientation and create intermediate files
echo "Fixing orientation for each file..."
normalized_files=()
for file in "${sorted_files[@]}"; do
  base_name=$(basename "$file" .mp4)
  normalized_file="$temp_dir/${base_name}_fixed.mp4"

  transpose_value=$(get_transpose_value "$file")
  if [ "$transpose_value" -eq 0 ]; then
    # No rotation needed
    cp "$file" "$normalized_file"
  else
    # Apply transpose filter for rotation
    ffmpeg -i "$file" \
      -vf "transpose=$transpose_value,setpts=PTS-STARTPTS" \
      -c:v libx264 -preset fast -crf 23 -c:a copy -y "$normalized_file"
  fi

  if [ $? -eq 0 ]; then
    normalized_files+=("$normalized_file")
  else
    echo "Error fixing orientation for file: $file. Skipping."
  fi
done

# Check if there are normalized files
if [ ${#normalized_files[@]} -eq 0 ]; then
  echo "No files were successfully normalized. Aborting."
  exit 1
fi

# Generate the file list for ffmpeg concatenation
echo "Generating file list for merging..."
> "$file_list"
for file in "${normalized_files[@]}"; do
  echo "file '$file'" >> "$file_list"
done

# Merge the normalized files into a single file
merged_file="$output_dir/${output_prefix}_merged_temp.mp4"
echo "Merging normalized files into a single video..."
ffmpeg -f concat -safe 0 -i "$file_list" -c:v libx264 -preset fast -crf 23 -c:a aac -b:a 192k -movflags +faststart -y "$merged_file"

# Check if the merging was successful
if [ $? -ne 0 ]; then
  echo "Error during merging. Aborting."
  exit 1
fi

# Finalize the merged video
final_output="$output_dir/${output_prefix}_merged_video.mp4"
echo "Finalizing the merged video..."
mv "$merged_file" "$final_output"

# Preserve the earliest creation date from the input files
if [[ "$OSTYPE" == "darwin"* ]]; then
  # macOS
  earliest_date=$(ls -tU "${sorted_files[@]}" | tail -n 1 | xargs stat -f "%B")
  touch -t "$(date -r "$earliest_date" +"%Y%m%d%H%M.%S")" "$final_output"
else
  # Linux
  earliest_date=$(stat -c "%W" "${sorted_files[0]}")
  touch -d "@$earliest_date" "$final_output"
fi

echo "Sorted files:"
for file in "${sorted_files[@]}"; do
  echo "$file"
done

echo "Merged video created: $final_output"

# Clean up temporary files
rm -f "$file_list"
rm -rf "$temp_dir"
echo "Temporary files removed."

echo "Done!"
