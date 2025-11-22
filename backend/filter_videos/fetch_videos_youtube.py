# fetch_videos_youtube.py
import sys
import os
from backend.youtube_videos.tasks import process_video_task
from asgiref.sync import sync_to_async

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from filter_videos.filter_pipeline import VideoFilter
from youtube_videos.youtube_fetcher import fetch_videos, process_video
from main_app.models import Topic, Video, Transcript, Question
from youtube_videos.utils import extract_video_id

import logging
logger = logging.getLogger(__name__)

async def fetching_videos(language: str, topic_name: str):
    videos = await sync_to_async(fetch_videos)(f"{language} {topic_name}", max_results=5)
    if not videos:
        logger.error("No videos fetched.")
        return
    
    topic_obj = await sync_to_async(Topic.objects.get)(
        name=topic_name, language__name=language
    )

    logger.info(f"Total videos fetched: {len(videos)}")
    new_video_list = []

    for vid in videos:
        video_id = extract_video_id(vid["url"])
        if not await found_video(video_id):
            new_video_list.append(vid)

    if not new_video_list:
        logger.info("No new videos to process.")
        return
    
    logger.info(f"Found {len(new_video_list)} new candidate videos. Applying AI filter...")

    MAX_CANDIDATES = 10
    new_video_list = new_video_list[:MAX_CANDIDATES]
    logger.info(f"Limiting filtering to {len(new_video_list)} videos (max {MAX_CANDIDATES})")

    vf = VideoFilter()
    filtered_videos = await sync_to_async(vf.filter_videos_batch)(new_video_list, language, topic_name)
    filtered_videos = filtered_videos[:8]

    logger.info(f"Final selection: {len(filtered_videos)} videos to process")

    current_count = await sync_to_async(lambda: topic_obj.videos.count())()

    if len(filtered_videos) > current_count:
        topic_obj.total_videos = len(filtered_videos)
        await sync_to_async(topic_obj.save)()
        
    topic_obj.is_fully_processed = True
    await sync_to_async(lambda: topic_obj.save())()

    logger.info("\nProcessing filtered videos...\n")

    for video in filtered_videos:
        await process_video(
            video['title'],
            video['description'],
            video['url'],
            topic_name,
        )

    logger.info(f"Enqueued {len(filtered_videos)} videos for full processing (transcribe + questions)")

async def found_video(video_ID: str) -> bool:
    """Return True only if video, transcript, and questions exist for this video_ID."""
    try:
        video_exists = await sync_to_async(Video.objects.filter(video_id=video_ID).exists)()
        if not video_exists:
            return False
        
        transcript_exists = await sync_to_async(
            Transcript.objects.filter(video__video_id=video_ID).exists
        )()
        
        question_exists = await sync_to_async(
            Question.objects.filter(video__video_id=video_ID).exists
        )()

        return video_exists and transcript_exists and question_exists
        
    except Exception as e:
        logger.error(f"Error checking video existence {video_ID}: {str(e)}")
        return False
