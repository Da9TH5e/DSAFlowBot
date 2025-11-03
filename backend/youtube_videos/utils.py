# backend/youtube_videos/utils.py
from urllib.parse import urlparse, parse_qs

LATEST_VIDEO_ID = None

def extract_video_id(youtube_url):
    """Extracts YouTube video ID from various URL formats."""
    global LATEST_VIDEO_ID
    video_id = None

    if not youtube_url:
        return None
        
    parsed = urlparse(youtube_url)
    
    # Handle standard URLs (www.youtube.com/watch?v=ID)
    if parsed.query:
        vid_param = parse_qs(parsed.query).get('v')
        if vid_param and vid_param[0]:
            video_id = vid_param[0]
    
    # Handle shortened URLs or embed formats
    if not video_id and parsed.path:
        video_id = parsed.path.split('/')[-1] or None

    if video_id:
        LATEST_VIDEO_ID = video_id
    
    return video_id

def get_latest_video_id() -> str:
    """Returns the most recently extracted video ID."""
    return LATEST_VIDEO_ID

