#! /Users/henry/projects/youtube/.youtube/bin/python

import os
import sys
import subprocess
from yt_dlp import YoutubeDL

def clean_filename(name: str) -> str:
    """
    Cleans a filename by removing forbidden characters and trimming length.
    :param name: Original filename.
    :return: Cleaned filename.
    """
    forbidden_chars = '"*\\/\'.|?:<>'
    filename = ''.join([c if c not in forbidden_chars else '_' for c in name]).strip()
    return filename[:170] + '...' if len(filename) >= 176 else filename

def construct_url(input_string: str) -> str:
    """
    Constructs a full YouTube URL if the input is a video ID.
    :param input_string: Video URL or video ID.
    :return: Full YouTube URL.
    """
    if input_string.startswith("http"):
        return input_string  # Already a full URL
    return f"https://www.youtube.com/watch?v={input_string}"  # Construct URL from video ID

def download_video(input_string: str, save_location: str, resolution: str = "1080p"):
    """
    Downloads a YouTube video using yt-dlp and merges video and audio streams.
    :param input_string: YouTube video URL or video ID.
    :param save_location: Directory to save the final video.
    :param resolution: Desired resolution (e.g., '1080p', '720p', 'best'). Defaults to '1080p'.
    """
    try:
        # Ensure the save location exists
        os.makedirs(save_location, exist_ok=True)

        # Construct URL and fetch video metadata
        video_url = construct_url(input_string)
        with YoutubeDL() as ydl:
            info = ydl.extract_info(video_url, download=False)
            video_title = clean_filename(info.get("title", "video"))

        # Temporary filenames for video, audio, and output
        video_file = os.path.join(save_location, "temp_video.mp4")
        audio_file = os.path.join(save_location, "temp_audio.mp4")
        output_file = os.path.join(save_location, f"{video_title}_{resolution}.mp4")

        # Define resolution-based format selection
        resolution_map = {
            "8K": "4320",
            "4K": "2160",
            "1440p": "1440",
            "1080p": "1080",
            "720p": "720",
            "480p": "480",
            "360p": "360",
            "240p": "240",
            "best": "best",
        }
        selected_resolution = resolution_map.get(resolution, "1080p")

        print(f"Downloading: {video_title} from {video_url} at resolution: {resolution}")

        # Download video stream
        subprocess.run(
            [
                "yt-dlp",
                "-f", f"bestvideo[height<={selected_resolution}]",  # Video stream only
                "-o", video_file,
                video_url,
            ],
            check=True,
        )

        # Download audio stream
        subprocess.run(
            [
                "yt-dlp",
                "-f", "bestaudio",  # Audio stream only
                "-o", audio_file,
                video_url,
            ],
            check=True,
        )

        # Combine video and audio using FFmpeg
        print("Combining video and audio streams...")
        merge_command = [
            "ffmpeg",
            "-i", video_file,
            "-i", audio_file,
            "-c", "copy",
            "-y",  # Overwrite output if exists
            output_file,
        ]
        subprocess.run(merge_command, check=True)

        print(f"Download complete! Video saved to: {output_file}")

        # Cleanup temporary files
        os.remove(video_file)
        os.remove(audio_file)

    except subprocess.CalledProcessError as e:
        print(f"Error during download or processing: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    # Ensure sufficient arguments are provided
    if len(sys.argv) < 2:
        print("Usage: python youtube_downloader.py <Video ID or URL> [Resolution (default: 1080p)]")
        sys.exit(1)

    # Extract arguments
    video_input = sys.argv[1]  # Video ID or Full URL
    resolution = sys.argv[2] if len(sys.argv) > 2 else "1080p"  # Resolution (default: 1080p)

    # Output folder for downloads
    output_folder = "youtube_videos"

    # Run the download function
    download_video(input_string=video_input, save_location=output_folder, resolution=resolution)