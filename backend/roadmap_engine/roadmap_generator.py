# roadmap_generator.py

from typing import Dict, List
from main_app.models import Language, Roadmap
from groq import Groq
import os
import logging
logger = logging.getLogger(__name__)

def generate_roadmap(language_name: str) -> Dict[str, List[str]]:
    language_name = language_name.lower()
    
    lang_obj, _ = Language.objects.get_or_create(name=language_name)
    
    existing_roadmap = Roadmap.objects.filter(language=lang_obj).first()
    if existing_roadmap and existing_roadmap.topics:

        topics = existing_roadmap.topics
        logger.info(f"Fetched existing roadmap for {language_name} from DB with {len(topics)} topics.")
        return {"topics": topics}
    
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    client = Groq(api_key=GROQ_API_KEY)

    prompt = f"""
        Generate a structured learning roadmap for {language_name}.
        The roadmap must follow this order:
        - Beginner topics first
        - Then Intermediate topics
        - Then Advanced topics

        Rules:
        - Only output plain topic names, one per line.
        - Do NOT add numbering, bullets, markdown, or arrows.
        - Do NOT include section headers like Beginner, Intermediate, or Advanced.
        - Do not include the language in the topics (e.g., "Introduction to c++" these are not correct)
        - Do not include numbers in the topics (e.g., "1. Introduction to Variables" these are not correct)
        - Topics must be unique
        - Maximum of 18 topics.

        Example output:
        Topic 1
        Topic 2
        Topic 3
        Topic 4
        Topic 5
    """

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a roadmap generator for learning programming languages."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.7
        )

        content = response.choices[0].message.content
        roadmap_topics = [
            line.strip()
            for line in content.split("\n")
            if line.strip() and not line.strip().endswith(":")
            and line.lower().strip() not in ["beginner", "intermediate", "advanced"]
        ]

        roadmap_obj = Roadmap.objects.create(language=lang_obj, topics=roadmap_topics)

        logger.info(f"Generated roadmap for {language_name} with {len(roadmap_topics)} topics.")
        return {"topics": roadmap_topics}

    except Exception as e:
        logger.error(f"Failed to generate roadmap: {str(e)}", exc_info=True)
        return {"error": str(e)}