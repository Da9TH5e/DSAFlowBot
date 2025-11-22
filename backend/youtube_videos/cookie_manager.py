# backend/youtube_videos/cookie_manager.py

import os
import yt_dlp
import random
import logging

logger = logging.getLogger(__name__)


def list_cookie_files(cookie_dir: str) -> list[str]:
    """Return a list of valid .txt cookie files."""
    if not cookie_dir or not os.path.exists(cookie_dir):
        logger.warning(f"Cookie directory not found: {cookie_dir}")
        return []

    return [
        os.path.join(cookie_dir, f)
        for f in os.listdir(cookie_dir)
        if f.endswith(".txt")
    ]


import sys

_last_progress = ""

def progress_hook(d):
    global _last_progress

    if d["status"] == "downloading":
        percent = d.get("_percent_str", "").strip()
        eta = d.get("_eta_str", "").strip()
        speed = d.get("_speed_str", "").strip()

        bar = f"[{percent}] Speed: {speed} ETA: {eta}"

        # Avoid duplicate redraws
        if bar != _last_progress:
            sys.stdout.write("\r" + bar)
            sys.stdout.flush()
            _last_progress = bar

    elif d["status"] == "finished":
        # Clear progress bar
        sys.stdout.write("\r" + " " * len(_last_progress) + "\r")
        sys.stdout.flush()

        logger.info(f"Download finished: {d.get('filename')}")


def download_with_cookie(url: str, cookie_file: str | None, output_path: str) -> bool:
    """
    Download ONLY audio → MP3, never MP4.
    """
    if os.path.exists(output_path):
        os.remove(output_path)

    # yt-dlp output template (same dir, forced .mp3)
    output_template = output_path.replace(".mp3", "")

    ydl_opts = {
        "cookiefile": cookie_file,
        "ignoreconfig": True,
        "noplugins": "all",
        "quiet": False,
        "no_warnings": False,
        "progress_hooks": [progress_hook],

        # 🔥 Force audio-only download (no video)
        "format": "bestaudio/best",

        # 🔥 Force direct MP3 conversion
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],

        # 🔥 Output path (yt-dlp will add .mp3)
        "outtmpl": output_template + ".%(ext)s",
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # yt-dlp will produce output_template.mp3
        final_mp3 = output_template + ".mp3"

        return os.path.exists(final_mp3)

    except Exception as e:
        logger.warning(f"Cookie failed ({cookie_file}): {e}")
        return False


def rotate_cookies_and_download(url: str, output_path: str, cookie_dir: str) -> bool:
    """
    Rotate cookies until download succeeds.
    Fallback: try without cookie.
    """
    cookies = list_cookie_files(cookie_dir)
    random.shuffle(cookies)

    logger.info(f"Found {len(cookies)} cookies for rotation.")

    # Try each cookie
    for cookie_file in cookies:
        if download_with_cookie(url, cookie_file, output_path):
            logger.info(f"SUCCESS with cookie: {cookie_file}")
            return True

    logger.warning("All cookies failed, trying WITHOUT cookie...")

    # Try without cookie
    if download_with_cookie(url, None, output_path):
        logger.info("Success WITHOUT cookie.")
        return True

    logger.error("Download failed with ALL methods.")
    return False
