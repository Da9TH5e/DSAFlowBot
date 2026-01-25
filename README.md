# 🧠 DSAFlowBot

**DSAFlowBot** is an intelligent assistant designed to streamline your Data Structures and Algorithms (DSA) practice. It generates topic-wise question flows, manages practice sessions, and helps you build a consistent routine with minimal friction.

👉 https://dsaflowbot.bar (server is under maintaince and might not work as intended it will be working by next week)
> ⚠️ Note: Due to limited server resources, performance may occasionally be slower.


### 🌐 Accessing the Live Application
You can acess the website by searching or clicking the above link

<img src="https://github.com/user-attachments/assets/e860c484-9b73-4ab4-9160-a5eacc128371" width="800"/>

---

## 🚀 Features
-  Auto-generated DSA question sets by topic and difficulty  
-  Intelligent question flow system for consistent practice  
-  JSON-based session logging  
-  Clean, optimized interface (currently for PC users only)

---

## 🧰 Tech Stack
- **Backend:** Django
- **Frontend:** HTML + CSS + Javascript  
- **Database:** SQLite  
- **AI Layer:** Python scripts for flow generation and question management  
- **Deployment:** Hosted on Hostinger server along with a custom domain  

---

## ⚙️ Current Status
| Component | Progress |
|------------|-----------|
| Backend | ✅ Completed |
| Database & Models | ✅ Completed |
| Frontend | ✅ Completed |
| Deployment | ✅ Completed |

---

## 🎥 End-to-End Product Walkthrough

This section demonstrates the complete user journey in DSAFlowBot — from first-time access to roadmap-driven DSA practice.

### 1. Entry Point & Dashboard Routing
When a user accesses the application, the system automatically routes them based on authentication state:
- Existing users are redirected to the login page
- New users are guided to the signup flow

### 2. Login Flow (Existing Users)
Authenticated users can securely log in to access their personalized dashboard.

<img src="https://github.com/user-attachments/assets/e638cc24-dc0d-4193-99d0-f79bcf300cfe" width="700" />


### 3. Signup Flow (New Users)
New users can create an account through a guided signup process.

<img src="https://github.com/user-attachments/assets/dbd4dd7c-c9f4-4451-8654-0ab45d20d1a3" width="700" />

During signup, users can choose a profile picture from six preloaded options served from the database.

<img src="https://github.com/user-attachments/assets/bd4ebfaa-c5b7-43a9-84e5-1008be21d378" />

After signup, users receive an email verification link to activate their account before accessing the dashboard.

<img width="500" height="250" alt="image" src="https://github.com/user-attachments/assets/1f2ac029-4e59-4cb1-8a70-b137eaff3ab1" />

### 6. Password Reset Flow
Users can recover access to their account using the password reset workflow.

<img src="https://github.com/user-attachments/assets/fba57409-9c81-41a5-87f8-7cc566182321" width="700"/>

### 7. Roadmap Generation
The core feature of DSAFlowBot automatically generates a structured, topic-wise DSA roadmap based on user input.

### 8. Topic Selection & Learning Order
Each roadmap breaks down topics and associated learning videos in a logical progression to support consistent practice.

<img src="https://github.com/user-attachments/assets/8e70227b-4780-4f13-b7a6-16e1e8072d4d" width="700" />


### 9. Practice Experience
Users follow the roadmap to practice DSA topics in sequence, maintaining continuity and reducing decision fatigue.


### 10. Roadmap Regeneration
If a user is not satisfied with the generated roadmap, they can regenerate a new one.  
Backend safeguards prevent regeneration during active processing.

<img src="https://github.com/user-attachments/assets/c60a499c-d6de-4ba6-a3b8-1d821dbe4e36" width="700"/>

---

## 🧑‍💻 Author
Developed by **Debarka Mandal** — blending AI, backend engineering, and DSA automation into one learning platform.

---

### ⭐ Support
If you like the project, consider **starring ⭐ the repo** to show support and stay updated!
Also if you want can suggest to add **features**
