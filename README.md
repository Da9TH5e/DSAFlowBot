# 🧠 DSAFlowBot

## 📝 Intro
**DSAFlowBot** is an intelligent assistant that helps you master Data Structures and Algorithms through auto-generated, topic-wise practice flows. It streamlines your DSA learning journey by providing a structured roadmap and consistent practice sessions with minimal friction.

👉 **Live:** https://dsaflowbot.bar

---

## 🧰 Tech Stack
- **Backend:** Django
- **Frontend:** HTML + CSS + JavaScript
- **Database:** SQLite
- **AI Layer:** Python scripts for roadmap and flow generation
- **Deployment:** Hostinger (custom domain)

---

## 🚀 Features (What Users Can Do)
- ✍️ **Sign up & authenticate** with email verification
- 🎨 **Choose profile pictures** from preloaded avatar options
- 🗺️ **Generate personalized DSA roadmaps** with AI-driven topic sequencing
- 📖 **Browse curated topics** with learning resources and difficulty levels
- 📝 **Practice structured flows** following the generated roadmap
- 🔄 **Regenerate roadmaps** if not satisfied with the initial plan
- 🔒 **Manage account** with password reset functionality

---

## ⚙️ Process (How It Works)

DSAFlowBot works through a **multi-phase pipeline** that transforms user input into a complete learning experience:

### System Architecture Diagram

```
PHASE 1: USER INPUT & AUTHENTICATION
┌──────────────────────────────────┐
│  User Login                      │
│  Select Language & Topic         │
└────────────┬─────────────────────┘
             │
             ▼
PHASE 2: ROADMAP & DEFINITION GENERATION
┌──────────────────────────────────────────┐
│  Send to AI Model API                    │
│  ├─ Generate Roadmap                     │
│  └─ Generate Definition (in selected     │
│     language & topic)                    │
└────────────┬─────────────────────────────┘
             │
             ▼
PHASE 3: YOUTUBE VIDEO DISCOVERY & FILTERING
┌──────────────────────────────────────────┐
│  Search YouTube for Topic Videos         │
│  Fetch Available Videos                  │
│  Filter Against Quality Rules            │
│  ├─ Video duration                       │
│  ├─ Channel credibility                  │
│  ├─ View count & ratings                 │
│  └─ Relevance score                      │
└────────────┬─────────────────────────────┘
             │
             ▼
PHASE 4: TRANSCRIPT & SUMMARY EXTRACTION
┌──────────────────────────────────────────┐
│  Collect Video Transcripts               │
│  ├─ IF Transcript Available              │
│  │  └─ Use Transcript                    │
│  └─ IF Transcript NOT Available          │
│     └─ Extract & Use Video Metadata      │
│        (Title, Description, etc.)        │
└────────────┬─────────────────────────────┘
             │
             ▼
PHASE 5: QUESTION GENERATION (with Token Management)
┌──────────────────────────────────────────┐
│  Generate Questions According to Rules   │
│  Check Token Count                       │
│  ├─ IF Tokens ≤ Limit                    │
│  │  └─ Generate Full Summary             │
│  └─ IF Tokens > Limit                    │
│     └─ PARTIAL METHOD:                   │
│        ├─ Divide Summary into Parts      │
│        ├─ Generate Questions per Part    │
│        └─ Combine Results                │
└────────────┬─────────────────────────────┘
             │
             ▼
PHASE 6: DATABASE STORAGE & DELIVERY
┌──────────────────────────────────────────┐
│  Save All Results to Database            │
│  ├─ Definitions                          │
│  ├─ Video Links & Metadata               │
│  ├─ Summaries/Transcripts                │
│  ├─ Generated Questions                  │
│  └─ Progress Tracking                    │
└────────────┬─────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────┐
│  Complete Roadmap Delivered to User      │
│  Topic → Definition → Videos → Questions │
└──────────────────────────────────────────┘
```

---

## 📚 What I Learned
- Building full-stack applications with Django + vanilla JavaScript
- Email verification flows and authentication patterns
- AI-driven content generation and roadmap logic
- Database design for multi-user platforms with SQLite
- Deployment and server management fundamentals
- User experience optimization for learning platforms

---

## 🎥 Demo Video
[Add your video link or demo video here]