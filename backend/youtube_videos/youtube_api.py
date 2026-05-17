#youtube_api.py

import os
import isodate
import requests
from youtube_transcript_api import YouTubeTranscriptApi

import logging
logger = logging.getLogger(__name__)


from asgiref.sync import sync_to_async
from dotenv import load_dotenv
load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

def search_youtube_videos(query):
    search_url = "https://www.googleapis.com/youtube/v3/search"
    search_params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": 50,
        "key": YOUTUBE_API_KEY
    }

    response = requests.get(search_url, params=search_params)
    if response.status_code != 200:
        logger.error(f"Error fetching YouTube videos: {response.status_code}")
        return []

    data = response.json()
    video_ids = [
        item["id"]["videoId"]
        for item in data.get("items", [])
        if item.get("id", {}).get("videoId")
    ]

    if not video_ids:
        logger.warning("No video IDs found in response.")
        return []

    details_url = "https://www.googleapis.com/youtube/v3/videos"
    details_params = {
        "part": "snippet,contentDetails",
        "id": ",".join(video_ids),
        "key": YOUTUBE_API_KEY
    }

    details_response = requests.get(details_url, params=details_params)
    if details_response.status_code != 200:
        logger.error(f"Error fetching video details: {details_response.status_code}")
        return []

    details_data = details_response.json()
    results = []

    for item in details_data.get("items", []):
        content = item.get("contentDetails", {})
        snippet = item.get("snippet", {})

        if content.get("caption") != "true":
            continue

        duration_str = content.get("duration")
        if not duration_str:
            continue

        try:
            duration = isodate.parse_duration(duration_str).total_seconds()
        except Exception as e:
            logger.warning(f"Skipping video {item['id']} due to duration parse error: {e}")
            continue

        if not (5 * 60 <= duration <= 2 * 60 * 60):
            continue

        results.append({
            "id": item["id"],
            "title": snippet.get("title", ""),
            "description": snippet.get("description", ""),
            "url": f"https://www.youtube.com/watch?v={item['id']}",
            "has_captions": True
        })

    return results


@sync_to_async
def get_youtube_transcript(video_id: str):
    try:
        entries = YouTubeTranscriptApi().fetch(video_id)
        transcript = " ".join(entry.text for entry in entries)
        return transcript if transcript else None
    except Exception as e:
        logger.warning(f"No transcript available for {video_id}: {e}")
        return None
