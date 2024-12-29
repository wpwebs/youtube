#! /Users/henry/projects/youtube/.youtube/bin/python

import sys
import subprocess
import re
from googleapiclient.discovery import build


def get_secret_from_1password(secret_ref: str) -> str:
    """Retrieve a secret from 1Password using the Secret Reference."""
    try:
        command = ["op", "read", secret_ref]
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error retrieving secret from 1Password: {e}")
        raise
    
def is_video_url(input_string):
    """
    Check if the input string is a YouTube video URL or video ID.
    """
    video_url_pattern = r"(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[a-zA-Z0-9_-]{11}"
    video_id_pattern = r"^[a-zA-Z0-9_-]{11}$"
    return re.match(video_url_pattern, input_string) or re.match(video_id_pattern, input_string)

def is_playlist_url(input_string):
    """
    Check if the input string is a YouTube playlist URL or playlist ID.
    """
    playlist_url_pattern = r"(https?://)?(www\.)?youtube\.com/.*[?&]list=([a-zA-Z0-9_-]+)"
    playlist_id_pattern = r"^[a-zA-Z0-9_-]+$"
    return re.match(playlist_url_pattern, input_string) or re.match(playlist_id_pattern, input_string)


def extract_playlist_id(input_string):
    """
    Extract the playlist ID from a YouTube playlist URL.
    """
    playlist_url_pattern = r"(https?://)?(www\.)?youtube\.com/.*[?&]list=([a-zA-Z0-9_-]+)"
    match = re.match(playlist_url_pattern, input_string)
    if match:
        return match.group(3)
    return input_string  # Assume input is already a playlist ID

def get_channel_id(input_string, api_key):
    """
    Resolves a YouTube input (channel ID, username, or handle) to a channel ID.
    :param input_string: Channel ID, username, or handle.
    :param api_key: YouTube Data API key.
    :return: Resolved Channel ID or None if invalid.
    """
    youtube = build("youtube", "v3", developerKey=api_key)

    # Regex to determine input type
    channel_id_pattern = r"^UC[a-zA-Z0-9_-]{22}$"
    username_pattern = r"^https?://(www\.)?youtube\.com/user/([^/?&]+)"
    handle_pattern = r"^https?://(www\.)?youtube\.com/@([^/?&]+)"

    # Check if input is already a channel ID
    if re.match(channel_id_pattern, input_string):
        return input_string

    # Check if input is a username URL
    match = re.match(username_pattern, input_string)
    if match:
        username = match.group(2)
        response = youtube.channels().list(part="id", forUsername=username).execute()
        if "items" in response and response["items"]:
            return response["items"][0]["id"]

    # Check if input is a handle URL
    match = re.match(handle_pattern, input_string)
    if match:
        handle = match.group(2)
        response = youtube.channels().list(part="id", forUsername=handle).execute()
        if "items" in response and response["items"]:
            return response["items"][0]["id"]

    # If no match, attempt search by custom URL or username directly
    try:
        response = youtube.search().list(part="snippet", q=input_string, type="channel").execute()
        if "items" in response and response["items"]:
            return response["items"][0]["snippet"]["channelId"]
    except Exception as e:
        print(f"Search error: {e}")

    return None

def get_channel_videos(channel_id, api_key):
    """
    Fetches all video IDs from a YouTube channel.
    """
    youtube = build("youtube", "v3", developerKey=api_key)
    video_ids = []

    try:
        response = youtube.channels().list(part="contentDetails", id=channel_id).execute()
        uploads_playlist_id = response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

        next_page_token = None
        while True:
            playlist_response = youtube.playlistItems().list(
                part="contentDetails",
                playlistId=uploads_playlist_id,
                maxResults=50,
                pageToken=next_page_token,
            ).execute()

            video_ids.extend(item["contentDetails"]["videoId"] for item in playlist_response.get("items", []))
            next_page_token = playlist_response.get("nextPageToken")
            if not next_page_token:
                break
    except Exception as e:
        print(f"Error fetching videos: {e}")

    return video_ids

def get_playlist_videos(playlist_id, api_key):
    """
    Fetches all video IDs from a YouTube playlist.
    """
    youtube = build("youtube", "v3", developerKey=api_key)
    video_ids = []

    try:
        next_page_token = None
        while True:
            playlist_response = youtube.playlistItems().list(
                part="contentDetails",
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token,
            ).execute()

            video_ids.extend(item["contentDetails"]["videoId"] for item in playlist_response.get("items", []))
            next_page_token = playlist_response.get("nextPageToken")
            if not next_page_token:
                break
    except Exception as e:
        print(f"Error fetching playlist videos: {e}")

    return video_ids

def clean_filename(name):
    """
    Cleans a filename by removing forbidden characters.
    """
    forbidden_chars = '"*\\/\'.|?:<>'
    return ''.join(c if c not in forbidden_chars else '_' for c in name).strip()

if __name__ == "__main__":
    # Retrieve API_KEY from 1Password
    API_KEY = get_secret_from_1password(secret_ref="op://dev/Henry Email/api_key")

    if len(sys.argv) < 2:
        print("Usage: python download_youtube.py <Video/Channel/Playlist> [Resolution (default: 1080p)]")
        sys.exit(1)

    input_value = sys.argv[1]

    if is_video_url(input_value):
        # Handle video download
        print(input_value)
    elif is_playlist_url(input_value):
        # Handle playlist download
        playlist_id = re.split(r"[?&]list=", input_value)[-1]
        video_ids = get_playlist_videos(playlist_id, API_KEY)
        print(f"\nTotal number of videos: {len(video_ids)}\n\nVideo IDs:")
        for video_id in video_ids:
            print(video_id)
    else:
        # Handle channel download
        channel_id = get_channel_id(input_value, API_KEY)
        if not channel_id:
            print("Failed to resolve channel ID.")
            sys.exit(1)

        video_ids = get_channel_videos(channel_id, API_KEY)
        print(f"\nTotal number of videos: {len(video_ids)}\n\nVideo IDs:")
        for video_id in video_ids:
            print(video_id)
