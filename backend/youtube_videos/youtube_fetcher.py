# youtube_videos/youtube_fetcher.py

import sys
import os
import logging

logger = logging.getLogger(__name__)

from main_app.models import Language, Video, Topic
from asgiref.sync import sync_to_async

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from question_generator.generator import generate_questions
from youtube_videos.utils import extract_video_id


async def process_video(video_title, video_desc, video_url, topic_name, language):
    logger.info(f"Processing: {video_url}")

    video_id = extract_video_id(video_url)
    if not video_id:
        logger.warning("Could not extract video_id. Skipping.")
        return

    lang_obj, _ = await sync_to_async(Language.objects.get_or_create)(
        name=language.lower()
    )

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

    inferred_context = f"""
    Programming Language: {language}
    Topic: {topic_name}

    Video Title:
    {video_title}

    Video Description:
    {video_desc}

    Note:
    No transcript is available. Infer reasonable programming
    questions based on topic and metadata only.
    """

    try:
        logger.info("Generating coding questions (metadata-only)...")
        await generate_questions(inferred_context, video_id)
    except Exception as e:
        logger.error(f"Error generating questions: {e}")
