# youtube_videos/groq_transcript_analysis.py

import os
from groq import Groq
import logging
logger = logging.getLogger(__name__)

def analyze_with_groq(
    transcript: str,  
    language: str,
    topic: str,
    title: str,
    description: str,
    tags: list
) -> bool:
    """
    FlowOne semantic relevance check (metadata-only).

    NOTE:
    - Transcript is intentionally ignored
    - Decision is based ONLY on title, description, and tags
    """

    try:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            logger.error("Groq API key not found.")
            return False

        client = Groq(api_key=api_key)

        prompt = f"""
        You are evaluating a YouTube video's METADATA.

        Task:
        Decide whether this video is an EDUCATIONAL programming tutorial
        that teaches the topic "{topic}" in the programming language "{language}".

        Video Metadata:
        Title: {title}
        Description: {description}
        Tags: {', '.join(tags)}

        Rules:
        - Return YES only if instructional intent is clear
        - Do NOT assume content not implied by metadata
        - Ignore clickbait, hype, or vague mentions
        - Reject if the topic is only mentioned in passing
        - Do NOT hallucinate

        Respond with ONLY one word:
        YES or NO
        """

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=3,
        )

        result = response.choices[0].message.content.strip().upper()

        if "YES" in result:
            logger.info(f"Groq confirms relevance → {title}")
            return True

        logger.info(f"Groq rejects relevance → {title}")
        return False

    except Exception as e:
        logger.error(f"Groq Analysis Error: {e}")
        return False
