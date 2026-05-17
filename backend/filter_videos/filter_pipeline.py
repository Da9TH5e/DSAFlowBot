# --- filter_videos/filter_pipeline.py ---

import os
import sys
from groq import Groq
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from typing import Dict, List

from youtube_videos.groq_transcript_analysis import analyze_with_groq

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

import logging
logger = logging.getLogger(__name__)

class VideoFilter:
    def filter_videos_batch(self, videos: List[Dict], language: str, topic: str) -> List[Dict]:
        """Filter videos in parallel with organized filtering stages."""
        lock = Lock()
        passed_videos = []
        failed_videos = []

        def process_video(video):
            try:
                if self._check_metadata(video, language, topic):
                    with lock:
                        passed_videos.append(video)
                    logger.info(f"Metadata passed: {video.get('title')}")
                else:
                    with lock:
                        failed_videos.append(video)
                    logger.info(f"Metadata failed: {video.get('title')}")
            except Exception as e:
                logger.error(f"Error processing video {video.get('title')}: {e}")

        logger.info("=== STAGE 1: Metadata Filtering ===")
        with ThreadPoolExecutor(max_workers=3) as executor:
            executor.map(process_video, videos)

        logger.info(f"Metadata results: {len(passed_videos)} passed, {len(failed_videos)} failed")

        if failed_videos:
            logger.info("=== STAGE 2: Caption Transcript Check (FlowOne) ===")
            for video in failed_videos:
                try:
                    if self._check_transcript(video, language, topic):
                        passed_videos.append(video)
                        logger.info(f"Transcript passed: {video.get('title')}")
                    else:
                        logger.info(f"Transcript failed (terminal): {video.get('title')}")
                except Exception as e:
                    logger.error(f"Transcript check error for {video.get('title')}: {e}")

        logger.info(f"Final results: {len(passed_videos)} total passed videos")
        return passed_videos

    def _check_metadata(self, video: Dict, language: str, topic: str) -> bool:
        """Relaxed metadata filtering for better recall."""
        logger.info(f"Checking metadata for: {video.get('title')}")

        language_norm = "c++" if language.lower() == "cpp" else language.lower()
        topic_norm = topic.lower()

        title = video.get('title', '').lower()
        description = video.get('description', '').lower()
        tags = [t.lower() for t in video.get('tags', [])]

        def fuzzy_match(text, words):
            return any(w in text for w in words)

        topic_variants = [topic_norm, topic_norm.rstrip('s'), topic_norm.replace('basic ', ''), topic_norm.replace(' ', '')]

        if language_norm in title or fuzzy_match(title, topic_variants):
            logger.info(f"Metadata title match: {video.get('title')}")
            return True

        if language_norm in description or fuzzy_match(description, topic_variants):
            logger.info("Metadata description match")
            return True

        if tags and any(language_norm in t or fuzzy_match(t, topic_variants) for t in tags):
            logger.info("Metadata tag match")
            return True

        logger.warning(f"No metadata match for: {video.get('title')}")
        return False
    
    def _check_transcript(self, video: Dict, language: str, topic: str) -> bool:
        """
        FlowOne Stage 2 check (AI semantic validation):
        - metadata-only
        - delegates to analyze_with_groq
        """
        logger.info(f"AI semantic metadata check for: {video.get('title')}")

        try:
            title = video.get("title", "")
            description = video.get("description", "")
            tags = video.get("tags", [])

            # transcript argument is intentionally empty (not used anymore)
            return analyze_with_groq(
                transcript="",
                language=language,
                topic=topic,
                title=title,
                description=description,
                tags=tags,
            )

        except Exception as e:
            logger.error(f"AI metadata validation failed: {e}")
            return False
