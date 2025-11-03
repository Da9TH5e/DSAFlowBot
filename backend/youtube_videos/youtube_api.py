#youtube_api.py

import os
import isodate
import requests

import logging
logger = logging.getLogger(__name__)

from dotenv import load_dotenv
load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

def search_youtube_videos(query, max_results):
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "key": YOUTUBE_API_KEY
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        logger.error(f"Error fetching YouTube videos: {response.status_code}")
        return []

    data = response.json()
    video_ids = [item["id"]["videoId"] for item in data.get("items", []) if "videoId" in item["id"]]
    if not video_ids:
        logger.error("No video IDs found in response.")
        return []
    
    details_url = "https://www.googleapis.com/youtube/v3/videos"
    details_params = {
        "part": "snippet,contentDetails",
        "id": ','.join(video_ids),
        "key": YOUTUBE_API_KEY
    }
    details_response = requests.get(details_url, params=details_params)
    if details_response.status_code != 200:
        logger.error(f"Error fetching video details: {details_response.status_code}")
        return []
    
    details_data = details_response.json()
    results = []
    for item in details_data.get("items", []):
        duration_str = item.get("contentDetails", {}).get("duration")
        
        if not duration_str:
            logger.warning(f"Skipping video {item['id']} due to missing duration")
            continue

        try:
            duration = isodate.parse_duration(duration_str).total_seconds()
        except Exception as e:
            logger.warning(f"Skipping video {item['id']} due to parse error: {e}")
            continue

        if 10 * 60 <= duration <= 60 * 60:
            results.append({
                "id": item["id"],
                "title": item["snippet"].get("title", ""),
                "description": item["snippet"].get("description", ""),
                "url": f"https://www.youtube.com/watch?v={item['id']}"
            })

    return results
    
    
async def get_youtube_transcript(video_id):
    url = f"https://www.youtube.com/api/timedtext?lang=en&v={video_id}"
    response = requests.get(url)

    if response.status_code != 200:
        return None

    try:
        import xml.etree.ElementTree as ET
        root = ET.fromstring(response.text)
        transcript = ' '.join([node.text for node in root.findall('.//text') if node.text])
        return transcript if transcript else None
    except Exception as e:
        logger.error(f"[Transcript Parsing Error] {e}")
        return None