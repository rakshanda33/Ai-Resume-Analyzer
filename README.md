# 📄 AI Resume Analyzer

> AI-powered resume analysis platform built with Python, Streamlit, and Google Gemini.

An intelligent resume review system that evaluates resumes, provides ATS optimization suggestions, rewrites weak resume bullets, and generates actionable feedback using Google's Gemini AI.

---

## 🚀 Current Features

| Feature | Description |
|----------|-------------|
| 📊 Resume Scoring | AI-generated resume score with hiring verdict |
| 💡 Detailed Feedback | Strengths, weaknesses, and improvement suggestions |
| 🎯 ATS Keyword Matcher | Compare resume against a job description |
| ✏️ AI Bullet Rewriter | Convert weak bullets into impactful achievements |
| 🧠 Gemini AI Analysis | Structured JSON-based AI responses |
| 📄 PDF Resume Upload | Extract and analyze resume content |
| ⚡ Error Handling | API key validation and quota handling |
| 🔄 Modern Gemini SDK | Migrated to latest `google-genai` package |

---

## 🛠 Tech Stack

- Python
- Streamlit
- Google Gemini API
- google-genai SDK
- PyPDF2
- Python-dotenv
- Git & GitHub

---

## 📂 Project Structure

```text
AI_Resume_Analyzer/
│
├── app.py
├── analyzer.py
├── prompts.py
├── utils.py
├── config.py
├── requirements.txt
├── README.md
└── .env
