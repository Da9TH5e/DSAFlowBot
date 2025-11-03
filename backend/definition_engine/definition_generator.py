# definition_engine/definition_generator.py

import os
import logging
from dotenv import load_dotenv
from groq import Groq
from main_app.models import Language, Topic, Definition

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

def generate_definition(language: str, topic: str) -> str:
    """
    Generate a short, beginner-friendly definition for a topic in a given language.
    Store/retrieve from DB automatically.
    """

    # Fix: create or get language and topic objects
    lang_obj, _ = Language.objects.get_or_create(name=language.lower())
    topic_obj, _ = Topic.objects.get_or_create(language=lang_obj, name=topic)

    # Check if definition already exists
    existing_def = Definition.objects.filter(topic=topic_obj).first()
    if existing_def:
        logger.info(f"Definition for '{topic}' in '{language}' already exists in DB.")
        return existing_def.definition

    # Prompt for Groq AI
    prompt = f"""
    Provide a clear, beginner-friendly definition of the topic "{topic}" in {language}.
    The definition must be in plain text, no markdown, no bullets.
    Keep it short and around 5 lines maximum.
    """

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a concise programming topic explainer."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.7,
        )

        content = response.choices[0].message.content.strip()

        # Save in DB
        Definition.objects.create(topic=topic_obj, definition=content)
        logger.info(f"Generated definition for '{topic}' in '{language}' and saved to DB.")

        return content

    except Exception as e:
        error_msg = f"Definition generation failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_msg