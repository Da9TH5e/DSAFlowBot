# youtube_videos/transcript_utils.py

import asyncio
from concurrent.futures import ThreadPoolExecutor
import shutil
from backend.youtube_videos.cookie_manager import rotate_cookies_and_download
from pydub import AudioSegment
import os
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_videos.audio_transcriber import transcribe_audio_with_whisper
import logging

from asgiref.sync import sync_to_async
from main_app.models import Transcript, Video

logger = logging.getLogger(__name__)

AUDIO_CACHE_DIR = os.path.join(os.path.dirname(__file__), "audio_cache")
os.makedirs(AUDIO_CACHE_DIR, exist_ok=True)
MAX_RETRIES = 3
RETRY_DELAY = 2

async def download_audio(video_url: str, video_id) -> list:
    """Download and split audio using cookie rotation."""
    loop = asyncio.get_event_loop()
    output_path = os.path.join(AUDIO_CACHE_DIR, f"{video_id}.mp3")
    cookie_dir = os.getenv("YTDLP_COOKIES_DIR", "cookies")

    if os.path.exists(output_path):
        os.remove(output_path)

    logger.info(f"Downloading audio for {video_id} with cookie rotation...")

    for attempt in range(MAX_RETRIES):
        try:
            success = await loop.run_in_executor(
                None,
                rotate_cookies_and_download,
                video_url,
                output_path,
                cookie_dir
            )

            if not success:
                logger.warning(f"Attempt {attempt+1}: Cookie rotation failed.")
                await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                continue

            if not os.path.exists(output_path):
                logger.error(f"Download success reported but file missing: {output_path}")
                return []

            with ThreadPoolExecutor() as executor:
                return await loop.run_in_executor(executor, split_audio_file, output_path)

        except Exception as e:
            logger.error(f"Error on attempt {attempt+1}: {e}")
            await asyncio.sleep(RETRY_DELAY * (attempt + 1))

    logger.error(f"ALL attempts failed for video {video_id}")
    return []


async def get_or_generate_transcript(video_url: str, video_id) -> str:
    """Async pipeline: transcript from YouTube or audio split and processed."""
    try:
        transcript_obj = await sync_to_async(Transcript.objects.get)(video__video_id=video_id)
        return transcript_obj.content
    except Transcript.DoesNotExist:
        pass

    transcript_text = None    
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        transcript_text = " ".join([t['text'] for t in transcript])

    except Exception as e:
        logger.warning(f"YouTube transcript fetch failed: {str(e)}")

    if not transcript_text:
        audio_paths = await download_audio(video_url, video_id)
        if not audio_paths:
            logger.error("Audio could not be downloaded or split.")
            return None

        transcript_text = ""
        for path in audio_paths:
            loop = asyncio.get_event_loop()
            part = await loop.run_in_executor(None, transcribe_audio_with_whisper, path)
            if part:
                transcript_text += part.strip() + "\n"
            cleanup_audio(path)
        transcript_text = transcript_text.strip()

    if transcript_text:
        video_obj, _ = await sync_to_async(Video.objects.get_or_create)(
            video_id=video_id, 
            defaults={"title": "Unknown"}
            )
        await sync_to_async(Transcript.objects.create)(video=video_obj, content=transcript_text)

    return transcript_text

def split_audio_file(file_path: str) -> list[str]:
    """Split audio into 2 parts and return the new file paths"""
    try:
        audio = AudioSegment.from_file(file_path)
        half_point = len(audio) // 2

        chunk1 = audio[:half_point]
        chunk2 = audio[half_point:]

        chunk1_path = file_path.replace(".mp3", "_part1.mp3")
        chunk2_path = file_path.replace(".mp3", "_part2.mp3")

        chunk1.export(chunk1_path, format="mp3")
        chunk2.export(chunk2_path, format="mp3")

        logger.info(f"Original duration: {len(audio)} ms")
        logger.info(f"Part 1: {len(chunk1)} ms, Part 2: {len(chunk2)} ms")

        return [chunk1_path, chunk2_path]
    except Exception as e:
        logger.error(f"Error splitting audio: {str(e)}")
        return []

def cleanup_audio(file_path: str):
    """Safe audio file cleanup with verification"""
    if not file_path:
        return
        
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up: {file_path}")
    except Exception as e:
        logger.warning(f"Could not clean up {file_path}: {str(e)[:200]}")

def complete_cleanup():
    """Cleanup all audio files in the cache directory"""
    if os.path.exists(AUDIO_CACHE_DIR):
        shutil.rmtree(AUDIO_CACHE_DIR)
        os.makedirs(AUDIO_CACHE_DIR, exist_ok=True)
        logger.info("Completed full audio cache cleanup.")