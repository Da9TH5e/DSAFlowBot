#video_filter_engine.py

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def detect_language_and_topic(text, selected_lang, selected_topic, lang_keywords, topic_keywords):
    language_match = any(
        kw.lower() in text.lower()
        for kw in lang_keywords.get(selected_lang, [])
    )
    topic_match = any(
        kw.lower() in text.lower()
        for kw in topic_keywords.get(selected_topic.lower(), [])
    )
    return language_match, topic_match
