# backend/youtube_videos/cookie_manager.py

import os
import yt_dlp
import logging
import sys

logger = logging.getLogger(__name__)

_last_progress = ""


def progress_hook(d):
    global _last_progress

    if d["status"] == "downloading":
        percent = d.get("_percent_str", "").strip()
        eta = d.get("_eta_str", "").strip()
        speed = d.get("_speed_str", "").strip()

        bar = f"[{percent}] Speed: {speed} ETA: {eta}"

        if bar != _last_progress:
            sys.stdout.write("\r" + bar)
            sys.stdout.flush()
            _last_progress = bar

    elif d["status"] == "finished":
        sys.stdout.write("\r" + " " * len(_last_progress) + "\r")
        sys.stdout.flush()
        logger.info(f"Download finished: {d.get('filename')}")


def download_with_cookie(url: str, cookie_file: str | None, output_path: str) -> bool:
    """
    Download audio as MP3.
    Cookies are intentionally ignored.
    Strategy:
    1) Audio-only
    2) Muxed fallback
    """

    if os.path.exists(output_path):
        os.remove(output_path)

    output_template = output_path.replace(".mp3", "")

    base_opts = {
        "ignoreconfig": True,
        "noplugins": "all",
        "quiet": False,
        "no_warnings": False,
        "progress_hooks": [progress_hook],
        "postprocessor_args": ["-threads", "1"],
        "outtmpl": output_template + ".%(ext)s",

        # ✅ Android client (most reliable on VPS)
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
        logger.info("Trying audio-only download...")
        ydl_opts = dict(base_opts)
        ydl_opts["format"] = "bestaudio/best"

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        if os.path.exists(output_template + ".mp3"):
            return True

    except Exception as e:
        logger.warning(f"Audio-only failed: {e}")

    # ---------- Attempt 2: muxed fallback ----------
    try:
        logger.info("Falling back to muxed download...")
        ydl_opts = dict(base_opts)  # no format forcing

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        return os.path.exists(output_template + ".mp3")

    except Exception as e:
        logger.warning(f"Muxed fallback failed: {e}")
        return False


def rotate_cookies_and_download(url: str, output_path: str, cookie_dir: str) -> bool:
    """
    Cookies are deprecated and intentionally disabled.
    Function kept for pipeline compatibility.
    """
    return download_with_cookie(url, None, output_path)
