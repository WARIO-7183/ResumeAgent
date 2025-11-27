# 🎯 Resume Scanner AI

> **AI-Powered Resume Screening Pipeline** — Automate candidate evaluation with multi-agent LLM orchestration

[![Python](https://img.shields.io/badge/Python-3.10+-3776ab?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![React](https://img.shields.io/badge/React-18-61dafb?style=for-the-badge&logo=react&logoColor=black)](https://reactjs.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agent_Orchestration-ff6b6b?style=for-the-badge)](https://github.com/langchain-ai/langgraph)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📤 **Direct Upload** | Upload a resume PDF and get instant AI evaluation |
| 📧 **Gmail Integration** | Auto-collect resumes from email attachments |
| 🗄️ **Supabase Storage** | Cloud storage for all collected resumes |
| 🤖 **Multi-Agent Evaluation** | Parallel AI agents assess skills, experience, culture fit |
| 📊 **Batch Scanning** | Evaluate multiple resumes at once with ranked results |
| 🎨 **Modern Web UI** | Beautiful React dashboard with dark theme |

---

## 🏗️ Architecture

```
                    ┌─────────────────────────────────────────┐
                    │            WEB APPLICATION              │
                    │  ┌─────────────┐    ┌───────────────┐  │
                    │  │   React     │◄──►│  Flask API    │  │
                    │  │  Frontend   │    │   Backend     │  │
                    │  └─────────────┘    └───────┬───────┘  │
                    └─────────────────────────────┼──────────┘
                                                  │
        ┌─────────────────────────────────────────┼─────────────────────┐
        │                                         ▼                     │
        │  ┌──────────────┐              ┌───────────────┐              │
        │  │    Gmail     │──────────────►│   Supabase   │              │
        │  │  Collector   │   uploads    │   Storage    │              │
        │  └──────────────┘              └───────┬───────┘              │
        │                                        │                      │
        │                                        ▼                      │
        │                         ┌──────────────────────────┐          │
        │                         │   LangGraph Pipeline     │          │
        │                         │  ┌────────────────────┐  │          │
        │                         │  │   Parse Resume     │  │          │
        │                         │  └─────────┬──────────┘  │          │
        │                         │            ▼             │          │
        │                         │  ┌────────────────────┐  │          │
        │                         │  │   Embed Resume     │  │          │
        │                         │  └─────────┬──────────┘  │          │
        │                         │            │             │          │
        │                         │   ┌────────┼────────┐    │          │
        │                         │   ▼        ▼        ▼    │          │
        │                         │ ┌───┐   ┌───┐   ┌───┐   │          │
        │                         │ │S1 │   │S2 │   │S3 │   │ Parallel │
        │                         │ └─┬─┘   └─┬─┘   └─┬─┘   │  Agents  │
        │                         │   │       │       │      │          │
        │                         │   ▼       ▼       ▼      │          │
        │                         │  ┌────────────────────┐  │          │
        │                         │  │    Aggregator      │  │          │
        │                         │  │   Final Score      │  │          │
        │                         │  └────────────────────┘  │          │
        │                         └──────────────────────────┘          │
        │                                                               │
        └───────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/yourusername/ResumeAgent.git
cd ResumeAgent

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file or update the config files:

```python
# supabase_client.py
SUPABASE_URL = "your-supabase-url"
SUPABASE_KEY = "your-supabase-key"

# langgraph_pipeline.py
api_key = "your-groq-api-key"

# resume_collector.py (for Gmail integration)
EMAIL_USER = "your-email@gmail.com"
EMAIL_PASS = "your-app-password"
```

### 3. Run the Application

**Backend:**
```bash
cd backend
pip install flask flask-cors
python app.py
```

**Frontend:**
```bash
cd frontend
npm install
npm start
```

Visit **http://localhost:3000** 🎉

---

## 📁 Project Structure

```
ResumeAgent/
├── 🐍 Core Pipeline
│   ├── langgraph_pipeline.py    # Multi-agent evaluation graph
│   ├── supabase_client.py       # Cloud storage client
│   └── resume_collector.py      # Gmail resume fetcher
│
├── 🖥️ Backend
│   └── backend/
│       ├── app.py               # Flask REST API
│       └── requirements.txt
│
├── 🎨 Frontend
│   └── frontend/
│       ├── src/
│       │   ├── App.js           # Main React component
│       │   └── App.css          # Styling
│       ├── public/
│       └── package.json
│
├── 📓 Notebooks
│   └── resume.ipynb             # Experimentation notebook
│
└── 📄 Config
    ├── requirements.txt
    ├── .gitignore
    └── README.md
```

---

## 🤖 Evaluation Agents

| Agent | What it Evaluates | Score |
|-------|-------------------|-------|
| 🎯 **Skill Match** | Proficiency in required skills (dynamic per skill) | 0-10 |
| 💼 **Experience** | Years, relevance, career progression | 0-10 |
| 🤝 **Culture Fit** | Teamwork, leadership, communication signals | 0-10 |
| 📋 **JD Match** | Alignment with job description | 0-10 |
| 📊 **Aggregator** | Weighted average of all scores | 0-10 |

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/folders` | List date folders in storage |
| `GET` | `/api/resumes?folder=` | List resumes in a folder |
| `POST` | `/api/upload` | Upload resume to storage |
| `POST` | `/api/scan` | Scan multiple resumes |
| `POST` | `/api/scan-upload` | Upload & scan immediately |

### Example: Scan Resumes

```bash
curl -X POST http://localhost:5000/api/scan \
  -H "Content-Type: application/json" \
  -d '{
    "storage_paths": ["2025-11-27/resume1.pdf", "2025-11-27/resume2.pdf"],
    "job_description": "Looking for a Python developer...",
    "skills": ["python", "django", "postgresql"]
  }'
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **LLM** | Groq API (LLaMA 3.3 70B) |
| **Orchestration** | LangGraph |
| **Embeddings** | HuggingFace `all-MiniLM-L6-v2` |
| **Backend** | Flask + Flask-CORS |
| **Frontend** | React 18 |
| **Storage** | Supabase |
| **Parsing** | pypdf, python-docx |

---

## 📸 Screenshots

### 🖥️ Direct Upload
Upload a PDF and get instant AI evaluation with detailed breakdown.

### 📧 Gmail Resumes
Browse collected resumes, select multiple, and batch scan.

### 📊 Results Dashboard
Ranked results with scores, grades, and detailed explanations.

---

## 🗺️ Roadmap

- [x] Core LangGraph pipeline
- [x] Gmail resume collection
- [x] Supabase integration
- [x] Flask REST API
- [x] React web interface
- [ ] Vector store for resume similarity search
- [ ] Email notifications for top candidates
- [ ] Export results to CSV/Excel
- [ ] Authentication & multi-user support

---

## 🤝 Contributing

Contributions welcome! Please feel free to submit a Pull Request.

---

## 📄 License

MIT License - feel free to use this project for your own purposes.

---

<p align="center">
  <b>Built with ❤️ using LangGraph + Groq + React</b>
</p>
