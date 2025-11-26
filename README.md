# Resume Screening Pipeline with LangGraph

An AI-powered resume evaluation system that uses multi-agent orchestration to analyze candidates against job requirements.

## Overview

This project implements an automated resume screening pipeline using **LangGraph** for agent orchestration and **Groq's LLaMA 3.3 70B** for intelligent evaluation. Multiple specialized agents run in parallel to assess different aspects of a candidate's profile.

## Architecture

```
┌─────────────────┐
│  Parse Resume   │  ← PDF/DOCX text extraction
└────────┬────────┘
         │
┌────────▼────────┐
│  Embed Resume   │  ← HuggingFace sentence embeddings
└────────┬────────┘
         │
    ┌────┴────┬──────────┬──────────┬──────────┐
    ▼         ▼          ▼          ▼          ▼
┌───────┐ ┌───────┐ ┌─────────┐ ┌────────┐ ┌────────┐
│Skill 1│ │Skill 2│ │Experience│ │Culture │ │JD Match│
│ Agent │ │ Agent │ │  Agent   │ │  Fit   │ │ Agent  │
└───┬───┘ └───┬───┘ └────┬────┘ └───┬────┘ └───┬────┘
    └─────────┴──────────┴──────────┴──────────┘
                         │
                ┌────────▼────────┐
                │   Aggregator    │  ← Final score (0-10)
                └─────────────────┘
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Agent Orchestration | LangGraph (StateGraph) |
| LLM | Groq API (LLaMA 3.3 70B) |
| Embeddings | HuggingFace `all-MiniLM-L6-v2` |
| Document Parsing | pypdf, python-docx |
| State Management | TypedDict with Annotated reducers |

## Key Techniques

### 1. **Parallel Agent Execution**
Multiple evaluation agents run simultaneously after embedding, reducing total processing time. LangGraph handles fan-out/fan-in automatically.

### 2. **Dynamic Skill Agents**
Skills are passed as parameters, and the pipeline dynamically creates dedicated agents for each skill using a factory pattern.

### 3. **State Reducers for Concurrency**
Uses `Annotated[Dict, merge_dicts]` to safely merge outputs from parallel agents without conflicts.

### 4. **Structured LLM Output**
Agents request JSON responses with `score` (0-10) and `explanation` fields for consistent parsing.

## Agents

| Agent | Purpose |
|-------|---------|
| **Parse Resume** | Extracts text from PDF/DOCX files |
| **Embed Resume** | Generates vector embeddings for semantic search |
| **Skill Match** | Evaluates proficiency in specific skills (dynamic) |
| **Experience Validation** | Assesses years, relevance, and career progression |
| **Culture Fit** | Evaluates teamwork, leadership, and communication signals |
| **JD Match** | Compares resume against job description |
| **Aggregator** | Computes weighted average of all scores |

## File Structure

```
├── resume.py              # Main pipeline code (standalone Python script)
├── resume.ipynb           # Jupyter notebook version for experimentation
├── langgraph_pipeline.py  # Additional pipeline utilities
├── resume_collector.py    # Resume collection utilities
├── supabase_client.py     # Supabase database client
├── requirements.txt       # Python dependencies
└── README.md
```

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file with your Groq API key:
```
GROQ_API_KEY=your_key_here
```

## Usage

### Running the Python script:
```bash
python resume.py
```

### Or import in your code:
```python
from resume import create_resume_graph

graph = create_resume_graph(
    skills=["python", "machine learning", "communication"],
    evaluate_experience=True,
    evaluate_culture=True,
    evaluate_jd=True
)

result = graph.invoke({
    "resume_path": "candidate_resume.pdf",
    "job_description": "Looking for a backend engineer...",
    "skills_required": ["python", "machine learning"],
    "agent_outputs": {}
})

print("Score:", result["final_score"])
print("Breakdown:", result["final_breakdown"])
```

## Current Status

✅ Core pipeline functional  
✅ Parallel agent execution  
✅ PDF/DOCX parsing  
✅ Multi-skill evaluation  
⬜ Vector store for resume similarity search  
⬜ Batch processing for multiple resumes  
⬜ Web UI / API endpoint  

## License

MIT

