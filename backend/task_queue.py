import threading
import queue
import logging

from asgiref.sync import async_to_sync
from backend.filter_videos.fetch_videos_youtube import fetching_videos
from main_app.models import Topic

logger = logging.getLogger(__name__)

task_queue = queue.Queue()
_worker_started = False
_worker_lock = threading.Lock()


def worker_loop():
    logger.info("FIFO background worker started")

    while True:
        language, topic_name = task_queue.get()

        try:
            topic = Topic.objects.select_for_update().get(
                name=topic_name,
                language__name=language
            )

            if topic.is_fully_processed:
                task_queue.task_done()
                continue

            topic.is_processing = True
            topic.save(update_fields=["is_processing"])

            # FULL PIPELINE
            async_to_sync(fetching_videos)(language, topic_name)

            topic.is_fully_processed = True
            topic.is_processing = False
            topic.save(update_fields=["is_fully_processed", "is_processing"])

            logger.info(f"Completed topic: {topic_name}")

        except Exception as e:
            logger.exception(f"Pipeline failed for {topic_name}: {e}")
            Topic.objects.filter(
                name=topic_name,
                language__name=language
            ).update(is_processing=False)

        finally:
            task_queue.task_done()


def start_worker_once():
    global _worker_started

    with _worker_lock:
        if _worker_started:
            return
        
        Topic.objects.filter(is_processing=True).update(is_processing=False)

        t = threading.Thread(
            target=worker_loop,
            daemon=True
        )
        t.start()
        _worker_started = True
