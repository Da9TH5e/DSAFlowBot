#question_generator/chunked_transcript_processor.py

import os
import time
from groq import Groq
import tiktoken
from question_generator.prompts import get_chunk_prompt

from main_app.models import Video, Question

import logging
logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

def count_tokens(text: str) -> int:
    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))

def chunk_text(text, max_tokens=6000):
    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(text)
    return [
        enc.decode(tokens[i:i + max_tokens]) 
        for i in range(0, len(tokens), max_tokens)
    ]

def process_transcript(video_id: str):
    """Process transcript stored in DB for a given video_id into coding questions."""
    
    try:
        video = Video.objects.get(video_id=video_id)
    except Video.DoesNotExist:
        logger.error(f"[ERROR] Video not found in DB for video_id={video_id}")
        return

    if Question.objects.filter(video=video).exists():
        logger.info(f"Questions for video {video_id} already exist in DB. Skipping generation.")
        return f"Questions already exist for video {video_id}"

    if not hasattr(video, "transcript") or not video.transcript:
        logger.error(f"[ERROR] No transcript found for video {video_id}")
        return

    transcript = video.transcript.content
    chunks = chunk_text(transcript, max_tokens=5000)
    client = Groq(api_key=GROQ_API_KEY)

    all_questions_text = []

    for i, chunk in enumerate(chunks, start=1):
        is_last = (i == len(chunks))
        prompt = get_chunk_prompt(chunk, i, len(chunks), is_last)

        max_retries = 3
        backoff = 10

        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                    max_tokens=800
                )
                break
            except Exception as e:
                if "429" in str(e) and attempt < max_retries - 1:
                    logger.warning(f"429 Too Many Requests, retrying in {backoff} sec...")
                    time.sleep(backoff)
                    backoff *= 2
                else:
                    logger.error(f"LLM request failed: {e}")
                    raise

        reply = response.choices[0].message.content.strip()
        if is_last:
            all_questions_text.append(reply)
        logger.info(f"Part {i}/{len(chunks)} processed.")

    Question.objects.create(
        video=video,
        questions="\n\n".join(all_questions_text)
    )
    logger.info(f"Saved questions for video {video_id}")