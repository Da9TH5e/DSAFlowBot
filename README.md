<img width="985" height="111" alt="DSAFlowBot" src="https://github.com/user-attachments/assets/1b11f7f5-f585-4f19-a00e-20aec99160e1" />

DSAFlowBot is an intelligent DSA practice assistant that generates structured, topic-wise question flows to reduce decision fatigue and help users practice Data Structures & Algorithms consistently.
The system focuses on guided progression rather than random problem solving.

Here you can acess the live link: https://dsaflowbot.bar/ 


## 🧰 Technologies Used
- `Django`
- `Python`
- `HTML`, `CSS`, `Javascript`
- `LLM`
- `LangChain`
- `API Integration`
- `SQLite` 

## ✨ Features

- DSAFlowBot automatically generates a structured, topic-wise roadmap for Data Structures and Algorithms based on the user’s selected preferences and experience level.
  This ensures a logical learning progression instead of random problem solving.  
- Topics are unlocked in sequence, enforcing focused learning and preventing context switching.
  This reduces decision fatigue and helps users build consistency in their practice routine.
- Users can regenerate their roadmap if they are unsatisfied with the current one.
  Backend safeguards ensure:
    - No regeneration during active processing
    - No accidental overwrites of in-progress sessions
    - Controlled execution to avoid duplicate tasks  
- User activity and roadmap states are tracked using JSON-based logging, enabling:
    - Session continuity across logins
    - Debug-friendly backend monitoring
    - Reliable recovery from partial or interrupted flows
- The platform includes a complete authentication workflow:
    - User signup with email verification
    - Secure login handling
    - Password reset via email to ensures account integrity while keeping onboarding friction low. 
  The interface is intentionally minimal and optimized for desktop DSA practice, focusing on clarity, readability, and reduced distractions.
- DSAFlowBot is designed with a backend-first architecture where all critical logic — including roadmap generation, topic sequencing, regeneration safeguards, and session continuity — is handled server-side. This ensures deterministic behavior, prevents inconsistent states caused by frontend actions, and makes the system easier to debug, extend, and maintain, with the frontend acting primarily as a presentation layer.

## 🚀 Process

1. ***User Entry & Topic Selection:***
  When a user enters the DSAFlowBot dashboard, they begin by selecting a **DSA topic** and a **preferred programming language**. These inputs define the learning context for the entire pipeline. Once confirmed, the topic–language pair is sent from the frontend to the backend as a structured request, initiating the content generation flow.

2. ***AI-Driven Definition & Roadmap Generation:***
  The backend forwards the selected topic and language to the AI layer using a controlled prompt. The AI model generates:
    - A concise topic definition
    - A structured, topic-wise roadmap for learning and practice
   
   The generated definition and roadmap are validated and then **persisted in the database**, ensuring consistency across sessions. Once stored, this data is sent back to the frontend for display on the user dashboard.

3. ***YouTube Video Discovery:***
  In parallel, the backend uses the topic and language to query YouTube for relevant learning videos. This results in a **candidate pool of videos**, which acts as the raw input set for further validation and processing.

4. ***Database Deduplication Check:***
  Each video in the candidate pool is first checked against the database:
    - If the video already exists **and its questions are already generated**, it is ignored to prevent duplication.
    - If the video does not exist in the database, it proceeds to the filtering pipeline.

   This step ensures efficient reuse of previously processed content.

5. ***Stage 1 Filtering: Metadata Validation:***
  In the first filtering stage, the system analyzes the video’s metadata:
    - Title
    - Description
    - Tags

   The topic and language are matched against this metadata to determine relevance. Videos that fail this check are **not immediately discarded** but are forwarded to a deeper validation stage.

6. ***Stage 2 Filtering: Transcript-Based Relevance Check:***
  For videos that fail metadata validation, the backend extracts a **short portion of the video transcript** (not the full transcript). This partial transcript is sent to the AI model, which evaluates whether the content is conceptually relevant to the selected topic and language.
    - If deemed irrelevant, the video is rejected.
    - If relevant, the video is approved for processing.

7. ***Keyword Expansion & Fallback Search:***
  If no suitable videos pass the initial filters, the AI generates **alternative keywords and synonymous terms** related to the topic. These keywords are then used to perform additional YouTube searches, increasing the likelihood of discovering high-quality, relevant content.

8. ***Video Processing & Storage:***
  Once a video passes all relevance checks:
    - The video metadata is stored in the database.
    - The system attempts to fetch the full transcript directly from YouTube.
  If a transcript is unavailable:
    - The video’s audio is downloaded.
    - The audio is passed through **Whisper** for speech-to-text transcription.
    - The generated transcript is then stored in the database.

9. ***Question Generation Pipeline:***
  The final transcript is sent to the AI model using a custom prompt designed for DSA comprehension. The model generates **topic-aligned questions** based strictly on the transcript content. These questions are validated and stored in the database, linked to the corresponding video and topic.

10. ***Serving Content to the User:***
  When the user begins practice:
    - Questions are fetched directly from the database
    - No real-time generation occurs during practice
    - The system serves pre-validated, pre-generated content for consistent performance and reliability

  This completes the end-to-end pipeline from topic selection to question delivery.

## 🎞️ Video
https://github.com/user-attachments/assets/ad7cdbaf-b42d-4eba-a281-d9f26eb81372




## Walkthrough


