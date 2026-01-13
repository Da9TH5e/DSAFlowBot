import os
import django
import time

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

from backend.youtube_videos.fetch_videos_youtube import fetching_videos
from backend.models import VideoJob  # or your job model

def worker_loop():
    while True:
        job = (
            VideoJob.objects
            .filter(status="pending")
            .order_by("created_at")
            .first()
        )

        if not job:
            time.sleep(2)
            continue

        job.status = "running"
        job.save(update_fields=["status"])

        try:
            fetching_videos(job.video_id)
            job.status = "done"
        except Exception as e:
            job.status = "failed"
            job.error = str(e)
        finally:
            job.save()

if __name__ == "__main__":
    worker_loop()
