#!/bin/bash

# Set the source directory containing .mts files and destination folder for .mp4 files
source_dir="/Volumes/Multimedia/Videos/Kids/Lucy"
output_dir="/Volumes/Multimedia/Videos/Kids/Lucy/mp4"

# Create the output directory if it doesn't exist
mkdir -p "$output_dir"

# Loop through all .mts files in the source directory
for file in "$source_dir"/*.mts; do
  # Check if the file exists
  if [ ! -f "$file" ]; then
    echo "No .mts files found in the source directory."
    exit 1
  fi

  # Extract the base file name without extension
  base_name=$(basename "$file" .mts)

  # Set the output file name
  output_file="$output_dir/$base_name.mp4"

  # Convert .mts to .mp4, preserving metadata
  echo "Converting $file to $output_file..."
#   ffmpeg -i "$file" -map_metadata 0 -metadata:s:v -c:v copy -c:a copy -movflags +faststart "$output_file"
  ffmpeg -i "$file" \
    -map 0:v:0 -map 0:a:0 \
    -c:v copy \
    -c:a aac -b:a 192k -ac 2 \
    -bsf:v h264_mp4toannexb -bsf:a aac_adtstoasc \
    -strict experimental \
    -err_detect ignore_err \
    -movflags +faststart \
    -y "$output_file"
  # Preserve the original creation date
  if [[ "$OSTYPE" == "darwin"* ]]; then
    # For macOS
    original_date=$(stat -f "%B" "$file")
    if [ $? -eq 0 ]; then
      touch -t "$(date -r "$original_date" +"%Y%m%d%H%M.%S")" "$output_file"
      echo "Preserved creation date for $output_file."
    else
      echo "Failed to preserve creation date for $output_file."
    fi
  else
    # For Linux
    original_date=$(stat -c "%W" "$file")
    if [ $? -eq 0 ]; then
      touch -d "@$original_date" "$output_file"
      echo "Preserved creation date for $output_file."
    else
      echo "Failed to preserve creation date for $output_file."
    fi
  fi

  echo "Conversion completed for $file."
done

echo "All .mts files have been converted to .mp4 with metadata preserved."
