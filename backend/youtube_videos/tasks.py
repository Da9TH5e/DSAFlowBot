from mysite.celery import app as celery_app

import asyncio
from backend.youtube_videos.youtube_fetcher import process_video as process_video_async
@celery_app.task(bind=True)
def process_video_task(self, video_title, video_desc, video_url, topic_name, language):
    """
    Background task wrapper that runs your existing async process_video().
    """
    try:
        return asyncio.run(process_video_async(video_title, video_desc, video_url, topic_name, language))
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(process_video_async(video_title, video_desc, video_url, topic_name, language))

