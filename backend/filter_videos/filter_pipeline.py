# --- filter_videos/filter_pipeline.py ---

import json
import os
import sys
import tempfile
import yt_dlp
from groq import Groq
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from typing import Dict, List
import ffmpeg

from youtube_videos.audio_transcriber import WhisperTranscriber
from youtube_videos.groq_transcript_analysis import analyze_with_groq
from youtube_videos.youtube_api import search_youtube_videos

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
            logger.info("=== STAGE 2: Processing Failed Videos ===")
            for video in failed_videos:
                try:
                    logger.info(f"Processing failed video: {video.get('title')}")
                    
                    if self._check_transcript(video, language, topic):
                        passed_videos.append(video)
                        logger.info(f"Transcript passed: {video.get('title')}")
                        continue
                    
                    if self._try_keyword_expansion(video, language, topic):
                        passed_videos.append(video)
                        logger.info(f"AI expansion passed: {video.get('title')}")
                        continue
                    
                    logger.info(f"All stages failed: {video.get('title')}")
                    
                except Exception as e:
                    logger.error(f"Error processing failed video {video.get('title')}: {e}")

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

        if language_norm in title and fuzzy_match(title, topic_variants):
            logger.info(f"Metadata title match: {video.get('title')}")
            return True

        if language_norm in description and fuzzy_match(description, topic_variants):
            logger.info("Metadata description match")
            return True

        if tags and any(language_norm in t and fuzzy_match(t, topic_variants) for t in tags):
            logger.info("Metadata tag match")
            return True

        logger.warning(f"No metadata match for: {video.get('title')}")
        return False

    def _check_transcript(self, video: Dict, language: str, topic: str) -> bool:
        """Check if video passes transcript analysis."""
        logger.info(f"Transcript analysis for: {video.get('title')}")

        title = video.get('title', '').lower()
        description = video.get('description', '').lower()
        tags = video.get('tags', [])
        
        try:
            video_id = video['url'].split('=')[-1]
            temp_audio_dir = tempfile.gettempdir()
            full_audio_path = os.path.join(temp_audio_dir, f"full_audio_{video_id}.mp3")
            short_audio_path = os.path.join(temp_audio_dir, f"short_audio_{video_id}.mp3")

            if not self._download_audio(video['url'], full_audio_path):
                return False

            if not self._trim_audio(full_audio_path, short_audio_path):
                self._cleanup_files([full_audio_path])
                return False

            transcriber = WhisperTranscriber()
            transcript = transcriber.transcribe_audio(short_audio_path)

            self._cleanup_files([full_audio_path, short_audio_path])

            if transcript and analyze_with_groq(transcript, language, topic, title, description, tags):
                logger.info("Transcript analysis detected relevant content")
                return True
            else:
                logger.warning("Transcript analysis did not detect relevant content")
                return False

        except Exception as e:
            logger.error(f"Transcript analysis failed: {e}")
            return False

    def _try_keyword_expansion(self, video: Dict, language: str, topic: str) -> bool:
        """AI keyword expansion and relaxed re-search if metadata and transcript fail."""
        logger.info(f"Starting keyword expansion for: {video.get('title')}")

        if not client:
            logger.error("Groq client not available.")
            return False

        try:
            language_norm = "c++" if language.lower() == "cpp" else language.lower()
            topic_norm = topic.lower()

            keywords = self._generate_expanded_keywords(language_norm, topic_norm)
            logger.info(f"Generated {len(keywords)} expanded keywords: {keywords}")

            for term in keywords:
                search_query = f"{language_norm} {term}"
                search_results = search_youtube_videos(search_query, max_results=5)
                if not search_results:
                    logger.debug(f"No results for expansion term: {term}")
                    continue

                for vid in search_results:
                    title = vid.get("title", "").lower()
                    desc = vid.get("description", "").lower()

                    if topic_norm in title or topic_norm in desc or any(t in title for t in keywords):
                        logger.info(f"Found via expanded search: {vid.get('title')}")
                        return True

            logger.warning("Keyword expansion found no relevant videos.")
            return False

        except Exception as e:
            logger.error(f"Keyword expansion failed: {e}")
            return False

    def _download_audio(self, url: str, output_path: str) -> bool:
        """Download audio from YouTube video."""
        ydl_opts = {
            'retries': 5,
            'fragment_retries': 5,
            'socket_timeout': 30,
            'nopart': True,
            'quiet': True,
            'extract_audio': True,
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': output_path.replace('.mp3', ''),
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            return os.path.exists(output_path)
        except Exception as e:
            logger.error(f"Audio download failed: {e}")
            return False

    def _trim_audio(self, input_path: str, output_path: str, duration: int = 300) -> bool:
        """Trim audio to specified duration."""
        try:
            (
                ffmpeg
                .input(input_path)
                .output(output_path, t=duration)
                .overwrite_output()
                .run(quiet=True)
            )
            return os.path.exists(output_path)
        except Exception as e:
            logger.error(f"Audio trimming failed: {e}")
            return False

    def _generate_expanded_keywords(self, language: str, topic: str) -> List[str]:
        """Generate expanded search keywords using AI."""
        prompt = f"""
        Generate 5-8 specific YouTube search phrases for programming tutorials about "{topic}" 
        in {language}. Focus on practical tutorial content.

        Requirements:
        - Include beginner and advanced terms
        - Include common mistakes and solutions  
        - Include specific syntax and examples
        - Return as JSON array only

        Example for "Python recursion":
        ["recursion in python tutorial", "python recursive function examples", 
        "python recursion for beginners", "how recursion works python", 
        "python recursion practice problems"]
        """

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=200,
        )

        text = response.choices[0].message.content.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        
        if "[" in text and "]" in text:
            start_idx = text.index("[")
            end_idx = text.index("]") + 1
            text = text[start_idx:end_idx]
        
        try:
            keywords = json.loads(text)
        except json.JSONDecodeError:
            keywords = [kw.strip("-•* ,\"' ") for kw in text.split("\n") if kw.strip()]
            keywords = [kw for kw in keywords if kw and not kw.startswith(('[', ']'))]

        if topic not in keywords:
            keywords.append(topic)
        if language not in keywords:
            keywords.append(language)

        return keywords[:8]

    def _cleanup_files(self, file_paths: List[str]):
        """Clean up temporary files."""
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                logger.warning(f"Could not remove temporary file {file_path}: {e}")