# question_generator/generator.py

from asgiref.sync import sync_to_async
from main_app.models import Video, Question
from question_generator.chunked_transcript_processor import count_tokens, process_transcript
import json
import os
from dotenv import load_dotenv
from langchain_core.runnables import RunnableSequence
from langchain_groq import ChatGroq
from .prompt_template import question_prompt

import logging
logger = logging.getLogger(__name__)

load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")
model_name = os.getenv("GROQ_MODEL_NAME", "llama-3.1-8b-instant")
llm = ChatGroq(model_name=model_name, api_key=groq_api_key, temperature=0.7)
chain = RunnableSequence(question_prompt | llm)


async def generate_questions(summary: str, video_id: str):

    video = await sync_to_async(Video.objects.get)(video_id=video_id)

    existing_qns = await sync_to_async(lambda: Question.objects.filter(video=video).first())()
    if existing_qns:
        logger.info(f"Questions already exist for video {video_id}, skipping generation.")
        return

    total_tokens = count_tokens(summary)
    logger.info(f"Total tokens in summary: {total_tokens}")

    if total_tokens > 5000:
        await sync_to_async(process_transcript)(video_id)
        logger.info("Processed transcript in chunks.")
        return
    else:
        raw_output = await sync_to_async(lambda: chain.invoke({"summary": summary}).content)()

        try:
            questions_json = json.loads(raw_output)
            questions_text = json.dumps(questions_json, indent=2)
        except json.JSONDecodeError:
            logger.error("LLM output is not valid JSON. Saving raw text.")
            questions_text = raw_output

        await sync_to_async(Question.objects.create)(video=video, questions=questions_text)
        logger.info(f"Saved questions blob for video {video_id}")

def process_trancript_sync(video_id: str):
    return sync_to_async(process_transcript)(video_id)