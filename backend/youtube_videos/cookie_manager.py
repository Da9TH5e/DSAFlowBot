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
    Download audio as MP3.
    Strategy:
    1) Try audio-only (cheap)
    2) Fallback to muxed video+audio (reliable)
    """

    if os.path.exists(output_path):
        os.remove(output_path)

    output_template = output_path.replace(".mp3", "")

    base_opts = {
        "cookiefile": cookie_file,
        "ignoreconfig": True,
        "noplugins": "all",
        "quiet": False,
        "no_warnings": False,
        "progress_hooks": [progress_hook],
        "postprocessor_args": ["-threads", "1"],
        "outtmpl": output_template + ".%(ext)s",
        
        "extractor_args": {
            "youtube": {
                "player_client": ["android"]
            }
        },
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }

    # ---------- Attempt 1: audio-only ----------
    try:
        ydl_opts = dict(base_opts)
        ydl_opts["format"] = "bestaudio/best"

        logger.info("Trying audio-only download...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        if os.path.exists(output_template + ".mp3"):
            return True

    except Exception as e:
        logger.warning(f"Audio-only failed ({cookie_file}): {e}")

    # ---------- Attempt 2: muxed fallback ----------
    try:
        ydl_opts = dict(base_opts)
        ydl_opts["format"] = "best"

        logger.info("Falling back to muxed download...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        return os.path.exists(output_template + ".mp3")

    except Exception as e:
        logger.warning(f"Muxed fallback failed ({cookie_file}): {e}")
        return False


def rotate_cookies_and_download(url: str, output_path: str, cookie_dir: str) -> bool:
    if download_with_cookie(url, None, output_path):
        logger.info("Success WITHOUT cookie.")
        return True

    cookies = list_cookie_files(cookie_dir)
    random.shuffle(cookies)

    logger.info(f"Found {len(cookies)} cookies for rotation.")

    for cookie_file in cookies:
        if download_with_cookie(url, cookie_file, output_path):
            logger.info(f"SUCCESS with cookie: {cookie_file}")
            return True

    logger.error("Download failed with ALL methods.")
    return False

