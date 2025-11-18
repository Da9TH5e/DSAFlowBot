import os
import logging

logger = logging.getLogger(__name__)

AUDIO_CACHE_DIR = os.path.join(os.path.dirname(__file__), "audio_cache")

def cleanup_video_audio(video_id: str):
    """
    Safely remove only audio files belonging to the given video_id.
    Deletes ANY file that starts with the video_id.
    """
    try:
        for filename in os.listdir(AUDIO_CACHE_DIR):
            if filename.startswith(video_id):
                full_path = os.path.join(AUDIO_CACHE_DIR, filename)
                try:
                    os.remove(full_path)
                    logger.info(f"Deleted temp audio: {full_path}")
                except Exception as e:
                    logger.error(f"Error deleting file {full_path}: {e}")
    except Exception as e:
        logger.error(f"Error in cleanup for {video_id}: {e}")
