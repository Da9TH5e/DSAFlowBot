# youtube_videos/audio_transcriber.py

import os
import whisper

import logging
logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY = 2

class WhisperTranscriber:
    model = whisper.load_model("base")
    """Handles audio transcription using Groq API with rate limiting and error handling"""
    
    def transcribe_audio(self, audio_path: str) -> str:
        """Handle transcription with proper response parsing"""
        if not audio_path or not os.path.exists(audio_path):
            logger.error(f"Audio file not found")
            return None
        
        try:
            import time

            start_time = time.time()
            print(f"Transcribing: {audio_path}")

            result = self.model.transcribe(audio_path, task="translate", language = "en")
            end_time = time.time()
            duration = end_time - start_time

            logger.info(f"Finished: {audio_path}")
            logger.info(f"Time taken: {duration:.2f} seconds")

            return result["text"]
        
        except Exception as e:
            logger.warning(f"Local transcription error: {str(e)[:200]}")
            return None
        
def transcribe_audio_with_whisper(audio_path: str) -> str:
    transcriber = WhisperTranscriber()
    return transcriber.transcribe_audio(audio_path)