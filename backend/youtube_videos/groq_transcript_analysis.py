# youtube_videos/groq_transcript_analysis.py

import os
from groq import Groq
import logging
logger = logging.getLogger(__name__)

def analyze_with_groq(transcript: str, language: str, topic: str, title: str, description: str, tags: list) -> bool:
    """
    Analyze video content using Groq API with two-step verification:
    1. Check transcript for explicit mention of both language and topic.
    2. If not found, check metadata (title, description, tags).
    Returns True if either check confirms relevance.
    """
    try:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            logger.error("Groq API key not found in environment variables.")
            return False

        client = Groq(api_key=api_key)

        transcript_prompt = f"""
        Analyze this programming video transcript and determine if it explicitly discusses BOTH:
        1. Programming Language: {language}
        2. Topic: {topic}

        Requirements:
        - Both must be explicitly mentioned or clearly discussed
        - Look for actual content, not just passing references
        - Focus on tutorial/educational content about these topics

        Transcript: 
        {transcript[:6000]}

        Respond with exactly "true" if both are properly covered, otherwise "false".
        """

        transcript_response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": transcript_prompt}],
            temperature=0,
            max_tokens=10,
        )

        transcript_result = transcript_response.choices[0].message.content.strip().lower()

        if "true" in transcript_result:
            logger.info(f"Groq: Transcript confirms {language} + {topic} → {title}")
            return True

        logger.info(f"Groq: Transcript doesn't confirm {language} + {topic} → {title}")

        metadata_prompt = f"""
        Analyze this video metadata and determine if the video is relevant to:
        - Programming in {language}
        - Topic: {topic}

        Consider:
        - Direct matches for "{topic}" in {language}
        - Related concepts and subtopics
        - Practical examples and tutorials
        - Overall programming context

        Video Metadata:
        Title: {title}
        Description: {description[:800]}
        Tags: {', '.join(tags[:15]) if tags else 'None'}

        Respond with exactly "true" if relevant, otherwise "false".
        """

        metadata_response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": metadata_prompt}],
            temperature=0,
            max_tokens=10,
        )

        metadata_result = metadata_response.choices[0].message.content.strip().lower()

        if "true" in metadata_result:
            logger.info(f"Groq: Metadata confirms {language} + {topic} → {title}")
            return True

        logger.info(f"Groq: Metadata doesn't confirm {language} + {topic} → {title}")
        return False

    except Exception as e:
        logger.error(f"Groq Analysis Error: {e}")
        return False