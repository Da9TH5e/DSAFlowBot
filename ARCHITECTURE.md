## 🚀 Process

1. <ins><strong><em>User Entry & Topic Selection:</em></strong></ins> 
  When a user enters the DSAFlowBot dashboard, they begin by selecting a **DSA topic** and a **preferred programming language**. These inputs define the learning context for the entire pipeline. Once confirmed, the topic–language pair is sent from the frontend to the backend as a structured request, initiating the content generation flow.

2. <ins><strong><em>AI-Driven Definition & Roadmap Generation:</em></strong></ins>
  The backend forwards the selected topic and language to the AI layer using a controlled prompt. The AI model generates:
    - A concise topic definition
    - A structured, topic-wise roadmap for learning and practice
   
   The generated definition and roadmap are validated and then **persisted in the database**, ensuring consistency across sessions. Once stored, this data is sent back to the frontend for display on the user dashboard.

3. <ins><strong><em>YouTube Video Discovery:</em></strong></ins>
  In parallel, the backend uses the topic and language to query YouTube for relevant learning videos. This results in a **candidate pool of videos**, which acts as the raw input set for further validation and processing.

4. <ins><strong><em>Database Deduplication Check:</em></strong></ins>
  Each video in the candidate pool is first checked against the database:
    - If the video already exists **and its questions are already generated**, it is ignored to prevent duplication.
    - If the video does not exist in the database, it proceeds to the filtering pipeline.

   This step ensures efficient reuse of previously processed content.

5. <ins><strong><em>Stage 1 Filtering: Metadata Validation:</em></strong></ins>
  In the first filtering stage, the system analyzes the video’s metadata:
    - Title
    - Description
    - Tags

   The topic and language are matched against this metadata to determine relevance. Videos that fail this check are **not immediately discarded** but are forwarded to a deeper validation stage.

6. <ins><strong><em>Stage 2 Filtering: Transcript-Based Relevance Check:</em></strong></ins>
  For videos that fail metadata validation, the backend extracts a **short portion of the video transcript** (not the full transcript). This partial transcript is sent to the AI model, which evaluates whether the content is conceptually relevant to the selected topic and language.
    - If deemed irrelevant, the video is rejected.
    - If relevant, the video is approved for processing.

7. <ins><strong><em>Keyword Expansion & Fallback Search:</em></strong></ins>
  If no suitable videos pass the initial filters, the AI generates **alternative keywords and synonymous terms** related to the topic. These keywords are then used to perform additional YouTube searches, increasing the likelihood of discovering high-quality, relevant content.

8. <ins><strong><em>Video Processing & Storage:</em></strong></ins>
  Once a video passes all relevance checks:
    - The video metadata is stored in the database.
    - The system attempts to fetch the full transcript directly from YouTube.
  If a transcript is unavailable:
    - The video’s audio is downloaded.
    - The audio is passed through **Whisper** for speech-to-text transcription.
    - The generated transcript is then stored in the database.

9. <ins><strong><em>Question Generation Pipeline:</em></strong></ins>
  The final transcript is sent to the AI model using a custom prompt designed for DSA comprehension. The model generates **topic-aligned questions** based strictly on the transcript content. These questions are validated and stored in the database, linked to the corresponding video and topic.

10. <ins><strong><em>Serving Content to the User:</em></strong></ins>
  When the user begins practice:
    - Questions are fetched directly from the database
    - No real-time generation occurs during practice
    - The system serves pre-validated, pre-generated content for consistent performance and reliability

  This completes the end-to-end pipeline from topic selection to question delivery.
