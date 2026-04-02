<img width="985" height="111" alt="DSAFlowBot" src="https://github.com/user-attachments/assets/1b11f7f5-f585-4f19-a00e-20aec99160e1" />

DSAFlowBot is an intelligent DSA practice assistant that generates structured, topic-wise question flows to reduce decision fatigue and help users practice Data Structures & Algorithms consistently.
The system focuses on guided progression rather than random problem solving.

Here you can access the live link: https://dsaflowbot.bar/ 

## ✨ Features
- Auto-generates topic-wise paths based on experience to ensure logical progression.
- Topics unlock in order to prevent context switching and decision fatigue.
- Allows roadmap resets with backend safeguards against duplicate or interrupted tasks.
- JSON logging tracks progress for seamless recovery and reliable monitoring.
- Full signup, email verification, and password reset workflow.
- Distraction-free, desktop-optimized interface focused on practice clarity.
- Server-side logic ensures deterministic behavior, data integrity, and easier maintenance

## 🧰 Technologies Used
- **Backend**: Django + Python
- **AI**: LLM (Groq), LangChain
- **Other**: YouTube API, Whisper, SQLite, HTML/CSS/JS

## 🚀 Features
- Users select a topic and language, triggering the backend to generate and persist a custom definition and structured roadmap via AI.
- The system fetches YouTube videos, deduplicates them against the database, and performs two-stage filtering (metadata and AI-based transcript analysis) to ensure relevance.
- If initial searches fail, the AI generates synonymous keywords to re-query YouTube and ensure high-quality content discovery.
- For approved videos, the system retrieves transcripts directly or uses Whisper AI for speech-to-text, storing all data for session continuity.
- The backend generates topic-aligned practice questions from the transcripts, serving this pre-validated content to the user for a low-latency, distraction-free experience.

For more detailed view of the process : [Detailed Process](ARCHITECTURE.md)

## 🎞️ Video
https://github.com/user-attachments/assets/2cf3ff0a-0fef-438d-915c-6b4a2bd008ff

## 🖥️ Quick Start (Local Setup)
```bash
git clone https://github.com/Da9TH5e/DSAFlowBot.git
cd DSAFlowBot
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

In `settings.py` make ALLOWED_HOSTS = "*"
