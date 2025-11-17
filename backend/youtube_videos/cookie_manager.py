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

    files = [
        os.path.join(cookie_dir, f)
        for f in os.listdir(cookie_dir)
        if f.endswith(".txt")
    ]

    return files


def download_with_cookie(url: str, cookiefile: str | None, output_path: str) -> bool:
    """Try downloading using one cookie file (or None). Return True/False."""
    if os.path.exists(output_path):
        os.remove(output_path)

    ydl_opts = {
        "cookiefile": cookiefile,
        "ignoreconfig": True,
        "noplugins": "all",
        "quiet": True,
        "no_warnings": True,
        "format": "bestaudio/best",
        "outtmpl": output_path.replace(".mp3", "") + ".%(ext)s",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        return os.path.exists(output_path)
    except Exception as e:
        logger.warning(f"Cookie failed ({cookiefile}): {e}")
        return False


def rotate_cookies_and_download(url: str, output_path: str, cookie_dir: str) -> bool:
    """
    Try each cookie file one by one until one works.
    If all fail -> fallback: try without cookies.
    """
    cookies = list_cookie_files(cookie_dir)
    random.shuffle(cookies)

    logger.info(f"Found {len(cookies)} cookies for rotation.")

    for cookiefile in cookies:
        if download_with_cookie(url, cookiefile, output_path):
            logger.info(f"SUCCESS with cookie: {cookiefile}")
            return True

    logger.warning("All cookies failed, trying WITHOUT cookie.")

    if download_with_cookie(url, None, output_path):
        logger.info("Success WITHOUT cookie.")
        return True

    logger.error("Download failed with ALL methods.")
    return False