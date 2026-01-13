import threading
import queue
import logging

from asgiref.sync import async_to_sync
from backend.filter_videos.fetch_videos_youtube import fetching_videos
from main_app.models import Topic
from django.db import transaction

logger = logging.getLogger(__name__)

# FIFO queue
task_queue = queue.Queue()
queued_tasks = set()

queue_lock = threading.Lock()
_worker_started = False
_worker_lock = threading.Lock()


def worker_loop():
    logger.info("FIFO background worker started")

    while True:
        user_id, language, topic_name = task_queue.get()

        with queue_lock:
            queued_tasks.discard((user_id, language, topic_name))

        try:
            with transaction.atomic():
                topic = Topic.objects.select_for_update().get(
                    name=topic_name,
                    language__name=language
                )

                if topic.is_fully_processed:
                    task_queue.task_done()
                    continue

                topic.is_processing = True
                topic.save(update_fields=["is_processing"])

            async_to_sync(fetching_videos)(language, topic_name)

            topic.is_fully_processed = True
            topic.is_processing = False
            topic.save(update_fields=["is_fully_processed", "is_processing"])

            logger.info(
                f"Completed topic: {topic_name} (user={user_id})"
            )

        except Exception as e:
            logger.exception(
                f"Pipeline failed for user={user_id}, topic={topic_name}: {e}"
            )
            Topic.objects.filter(
                name=topic_name,
                language__name=language
            ).update(is_processing=False)

        finally:
            task_queue.task_done()


def upsert_user_task(user_id: int, language: str, topic_name: str):
    """
    Rules:
    - same user + same topic → no change
    - same user + different topic → replace queued task
    - running task is NOT touched
    """
    new_key = (user_id, language, topic_name)

    with queue_lock:
        if new_key in queued_tasks:
            return "unchanged"

        new_queue = queue.Queue()

        while not task_queue.empty():
            item = task_queue.get_nowait()
            queued_user_id, _, _ = item

            if queued_user_id == user_id:
                queued_tasks.discard(item)
            else:
                new_queue.put(item)

        while not new_queue.empty():
            task_queue.put(new_queue.get())

        queued_tasks.add(new_key)
        task_queue.put(new_key)

        return "replaced"


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
