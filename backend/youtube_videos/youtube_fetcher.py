#youtube_videos/youtube_fetcher.py

import asyncio
import sys
import os
import tempfile

import logging
logger = logging.getLogger(__name__)

from main_app.models import Language, Transcript, Video, Topic
from asgiref.sync import sync_to_async

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from question_generator.generator import generate_questions
from youtube_videos.transcript_utils import get_or_generate_transcript
from youtube_videos.youtube_api import search_youtube_videos, get_youtube_transcript
from youtube_videos.utils import extract_video_id
from youtube_videos.cleanup_utils import cleanup_video_audio

async def process_video(video_title, video_desc, video_url, topic_name, language):
    logger.info(f"Processing: {video_url}")


    video_id = extract_video_id(video_url)
    lang_obj, _ = await sync_to_async(Language.objects.get_or_create)(name=language.lower())
    topic, _ = await sync_to_async(Topic.objects.get_or_create)(
        language=lang_obj,
        name=topic_name
    )

    video, _ = await sync_to_async(Video.objects.get_or_create)(
        video_id=video_id,
        defaults={
            "title": video_title,
            "description": video_desc,
            "url": video_url,
            "topic": topic,
        }
    )

    try:
        transcript_obj = await sync_to_async(lambda: video.transcript)()
        transcript = transcript_obj.content
        logger.info("Transcript already exists in DB")
    except Transcript.DoesNotExist:
        transcript = None
        logger.info("No existing transcript found.")

    if not transcript:
        transcript = await get_youtube_transcript(video_id)


    if not transcript:
        logger.info("No transcript via YouTube API, trying audio transcription...")
        transcript = await get_or_generate_transcript(video_url, video_id)

    if transcript:
        transcript_obj, _ = await sync_to_async(Transcript.objects.update_or_create)(
            video=video,
            defaults={"content": transcript}
        )
        logger.info("Transcript saved/updated in DB.")

    if transcript:
        max_retries = 5
        backoff = 5
        for attempt in range(max_retries):
            try:
                logger.info("Generating coding questions...")
                await generate_questions(transcript, video_id)
                break
            except Exception as e:
                if "429" in str(e) and attempt < max_retries - 1:
                    logger.warning(f"429 Too Many Requests, retrying in {backoff} sec...")
                    await asyncio.sleep(backoff)
                    backoff *= 2
                else:
                    logger.error(f"Error generating questions: {e}")
                    break

    try:
        cleanup_video_audio(video_id)
        logger.info(f"Cleaned temp audio files for video {video_id}.")
    except Exception as e:
        logger.error(f"Audio cleanup error for {video_id}: {e}")


def fetch_videos(query, max_results=10):
    return search_youtube_videos(query, max_results)

