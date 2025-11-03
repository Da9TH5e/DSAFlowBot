# fetch_videos_youtube.py
import shutil
import sys
import os
from asgiref.sync import sync_to_async

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from filter_videos.filter_pipeline import VideoFilter
from youtube_videos.youtube_fetcher import fetch_videos, process_video
from main_app.models import Topic, Video, Transcript, Question
from youtube_videos.utils import extract_video_id

import logging
logger = logging.getLogger(__name__)

async def fetching_videos(language: str, topic_name: str):

    videos = await sync_to_async(fetch_videos)(f"{language} {topic_name}", max_results=20)
    if not videos:
        logger.error("No videos fetched.")
        return
    
    topic_obj = await sync_to_async(Topic.objects.get)(
        name=topic_name, language__name=language
    )

    logger.info(f"Total videos fetched: {len(videos)}")
    new_video_list = []

    for vid in videos:
        video_url = vid.get("url")
        video_ID = extract_video_id(video_url)
            
        if await found_video(video_ID):
            logger.info(f"Bool value :{await found_video(video_ID)}")
            logger.info(f"Skipping (already fully processed): {vid.get('title')}")
            continue
        else:
            new_video_list.append(vid)

    if not new_video_list:
        logger.info("No new videos to process.")
        return
    
    logger.info(f"{(new_video_list)}")

    vf = VideoFilter()
    filtered_videos = await sync_to_async(vf.filter_videos_batch)(new_video_list, language, topic_name)

    current_count = await sync_to_async(lambda: topic_obj.videos.count())()
    total_filtered_videos = len(filtered_videos)

    if total_filtered_videos > current_count:
        topic_obj.total_videos = total_filtered_videos
        await sync_to_async(topic_obj.save)()
        
    topic_obj.is_fully_processed = True
    await sync_to_async(lambda: topic_obj.save())()

    logger.info("\nProcessing filtered videos...\n")
    for video in filtered_videos:
        logger.info(f"Processing {video['title']}")
        await process_video(video['title'], video['description'], video['url'], topic_name, language)

    audio_cache_path = os.path.join(
        os.path.dirname(__file__), 
        "..", "youtube_videos", "audio_cache"
    )
    audio_cache_path = os.path.abspath(audio_cache_path)

    if os.path.exists(audio_cache_path):
        try:
            shutil.rmtree(audio_cache_path)
            logger.info(f"Cleaned up audio_cache folder: {audio_cache_path}")
        except Exception as e:
            logger.error(f"Error removing audio_cache folder: {e}")
    else:
        logger.info("audio_cache folder does not exist — skipping cleanup.")



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
