from __future__ import annotations
from typing import Dict, List, Any, Optional, TypedDict, Annotated
import os
import json
from operator import or_
from supabase_client import list_resumes_in_supabase, download_resume_from_supabase
from langgraph.graph import StateGraph, END
from langchain_groq.chat_models import ChatGroq
from langchain_community.embeddings import HuggingFaceEmbeddings
from pypdf import PdfReader
from docx import Document
import pytesseract
from dotenv import load_dotenv
from pydantic import BaseModel, Field    
from groq import Groq


def merge_dicts(a: dict, b: dict) -> dict:
    """Reducer to merge agent_outputs from parallel nodes."""
    return {**a, **b}


class ResumeState(TypedDict, total=False):
    resume_path: str
    skills_required: List[str]
    evaluate_experience: bool
    evaluate_culture_fit: bool
    job_description: str
    resume_text: str
    resume_embedding: List[float]
    agent_outputs: Annotated[Dict[str, Dict[str, Any]], merge_dicts]
    final_score: float
    final_breakdown: Dict[str, float]


def parse_resume_agent(state: ResumeState) -> dict:
    resume_path = state.get("resume_path")

    if not resume_path or not os.path.exists(resume_path):
        raise ValueError("Resume file path is invalid or file not found.")

    text = ""
    # PDF Parsing
    if resume_path.lower().endswith(".pdf"):
        reader = PdfReader(resume_path)
        for page in reader.pages:
            text += page.extract_text() + "\n"

    # DOCX Parsing
    elif resume_path.lower().endswith(".docx"):
        doc = Document(resume_path)
        for para in doc.paragraphs:
            text += para.text + "\n"

    else:
        raise ValueError("Unsupported file format. Only PDF/DOCX allowed.")

    # Clean text
    clean_text = text.strip().replace("\t", " ")

    return {"resume_text": clean_text}


embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


def embed_resume_agent(state: ResumeState) -> dict:
    resume_text = state.get("resume_text")
    if not resume_text:
        raise ValueError("Resume text not available. Parse step not completed.")

    # Generate embeddings from the extracted resume text
    vector = embedding_model.embed_query(resume_text)
    return {"resume_embedding": vector}


llm = ChatGroq(
    api_key="",
    model="llama-3.3-70b-versatile"
)


def skill_match_agent(skill: str):
    """
    Factory function that creates a dedicated skill evaluator agent
    using ChatGroq via LangChain.
    """

    def agent(state: ResumeState) -> dict:
        resume_text = state.get("resume_text")
        if not resume_text:
            raise ValueError("Resume text missing. Run parsing first.")

        prompt = f"""
You are an expert resume evaluator.

Here is the candidate's resume:
---
{resume_text}
---

Evaluate the candidate's proficiency in the skill: "{skill}".

Return STRICTLY a JSON object with:
- score: an integer from 0 to 10
- explanation: a short 1-sentence justification

Example format:
{{
  "score": 8,
  "explanation": "Strong evidence of experience with Python."
}}
"""

        response = llm.invoke(prompt)
        raw_output = response.content.strip()

        try:
            result = json.loads(raw_output)
        except Exception:
            result = {
                "score": 0,
                "explanation": f"Invalid JSON returned for skill '{skill}'. Raw output: {raw_output}"
            }

        return {"agent_outputs": {f"skill_{skill.lower().replace(' ', '_')}": result}}

    return agent


def experience_validation_agent(state: ResumeState) -> dict:
    resume_text = state.get("resume_text")
    if not resume_text:
        raise ValueError("Resume text missing. Run parsing first.")

    prompt = f"""
You are a professional HR domain expert.

Analyze the candidate's resume below:
---
{resume_text}
---

Evaluate the candidate's EXPERIENCE level based on:
1. Total years of experience
2. Relevance to industry and job roles
3. Seniority & responsibilities handled
4. Stability (frequency of job changes)
5. Consistency and clarity of career progression

Give a score strictly between 0 and 10 (integer only).

Return STRICTLY a JSON object with:
- score: integer 0–10
- explanation: 1 brief sentence justification

Example:
{{
  "score": 7,
  "explanation": "Candidate has around 3 years of relevant software development experience."
}}
"""

    response = llm.invoke(prompt)
    raw_output = response.content.strip()

    try:
        result = json.loads(raw_output)
    except:
        result = {
            "score": 0,
            "explanation": f"Invalid JSON for experience evaluation. Raw output: {raw_output}"
        }

    return {"agent_outputs": {"experience_validation": result}}


def culture_fit_agent(state: ResumeState) -> dict:
    resume_text = state.get("resume_text")
    if not resume_text:
        raise ValueError("Resume text missing. Run parsing first.")

    prompt = f"""
You are an HR expert trained to evaluate cultural fit in organizations.

Analyze this resume:
---
{resume_text}
---

Evaluate the candidate's CULTURE FIT based on:
1. Communication style and clarity
2. Teamwork and collaboration signals
3. Leadership traits (if any)
4. Work ethic and adaptability
5. Passion, initiative, ownership qualities
6. Alignment with general corporate values

Give a score strictly between 0 and 10 (integer only).

Return STRICTLY a JSON object with:
- score: integer from 0–10
- explanation: one short sentence

Example:
{{
  "score": 8,
  "explanation": "Shows strong teamwork, leadership, and communication alignment."
}}
"""

    response = llm.invoke(prompt)
    raw_output = response.content.strip()

    try:
        result = json.loads(raw_output)
    except:
        result = {
            "score": 0,
            "explanation": f"Invalid JSON for culture fit evaluation. Raw output: {raw_output}"
        }

    return {"agent_outputs": {"culture_fit": result}}


def jd_match_agent(state: ResumeState) -> dict:
    resume_text = state.get("resume_text")
    job_description = state.get("job_description")
    if not resume_text:
        raise ValueError("Resume text missing. Run parsing first.")
    if not job_description:
        raise ValueError("Job description missing. Provide JD before running this agent.")

    prompt = f"""
You are a professional HR evaluator.

Below is the JOB DESCRIPTION:
---
{job_description}
---

Below is the candidate's RESUME:
---
{resume_text}
---

Evaluate how well this candidate matches the JD based on:
1. Required skills
2. Relevant experience
3. Responsibilities alignment
4. Technical and soft skills match
5. Domain-specific fit
6. Overall suitability for the role

Give a score STRICTLY between 0 and 10 (integer only).

Return STRICTLY a JSON object:
{{
  "score": <0-10>,
  "explanation": "<1 sentence explanation>"
}}
"""

    response = llm.invoke(prompt)
    raw_output = response.content.strip()

    try:
        result = json.loads(raw_output)
    except:
        result = {
            "score": 0,
            "explanation": f"Invalid JSON for JD match evaluation. Raw output: {raw_output}"
        }

    return {"agent_outputs": {"jd_match": result}}


def aggregator_agent(state: ResumeState) -> dict:
    """
    Aggregates all scores from all agents (dynamic skill agents + fixed agents)
    and produces a final score between 0 and 10.
    """

    outputs = state.get("agent_outputs", {})

    if not outputs:
        raise ValueError("No agent outputs found. Nothing to aggregate.")

    total_score = 0
    count = 0
    breakdown = {}

    # Loop through all agents' results
    for agent_name, result in outputs.items():
        try:
            score = int(result.get("score", 0))
        except:
            score = 0  # if invalid score returned by LLM

        # Store score in breakdown
        breakdown[agent_name] = score

        total_score += score
        count += 1

    # Compute final 0–10 average
    if count > 0:
        final_score = round(total_score / count, 2)
    else:
        final_score = 0

    return {"final_score": final_score, "final_breakdown": breakdown}


def create_resume_graph(skills: list, evaluate_experience=True, evaluate_culture=True, evaluate_jd=True):
    """
    Creates the full LangGraph pipeline dynamically based on HR input.
    """

    # Initialize the graph with ResumeState
    graph = StateGraph(ResumeState)

    # -----------------------------
    # Add Fixed Nodes
    # -----------------------------
    graph.add_node("parse_resume", parse_resume_agent)
    graph.add_node("embed_resume", embed_resume_agent)

    # Experience & Culture Fit agents (only added if required)
    if evaluate_experience:
        graph.add_node("experience_validation", experience_validation_agent)

    if evaluate_culture:
        graph.add_node("culture_fit", culture_fit_agent)

    if evaluate_jd:
        graph.add_node("jd_match", jd_match_agent)

    # -----------------------------
    # Add Dynamic Skill Nodes
    # -----------------------------
    skill_nodes = []

    for skill in skills:
        node_name = f"skill_{skill.lower().replace(' ', '_')}"
        graph.add_node(node_name, skill_match_agent(skill))
        skill_nodes.append(node_name)

    # -----------------------------
    # Entry Point
    # -----------------------------
    graph.set_entry_point("parse_resume")

    # -----------------------------
    # Sequential: parse → embed
    # -----------------------------
    graph.add_edge("parse_resume", "embed_resume")

    # -----------------------------
    # Parallel Edges: embed → skill nodes
    # -----------------------------
    for node in skill_nodes:
        graph.add_edge("embed_resume", node)

    # Parallel Edges: embed → fixed nodes
    if evaluate_experience:
        graph.add_edge("embed_resume", "experience_validation")

    if evaluate_culture:
        graph.add_edge("embed_resume", "culture_fit")

    if evaluate_jd:
        graph.add_edge("embed_resume", "jd_match")

    # -----------------------------
    # Aggregator Node
    # -----------------------------
    graph.add_node("aggregate", aggregator_agent)

    # All nodes converge into the aggregator
    fan_in_nodes = skill_nodes.copy()

    if evaluate_experience:
        fan_in_nodes.append("experience_validation")

    if evaluate_culture:
        fan_in_nodes.append("culture_fit")

    if evaluate_jd:
        fan_in_nodes.append("jd_match")

    # Connect all evaluation nodes → aggregate
    for node in fan_in_nodes:
        graph.add_edge(node, "aggregate")

    # End of graph
    graph.add_edge("aggregate", END)

    # Finalize
    return graph.compile()

if __name__ == "__main__":
    # 1. Create the graph once
    graph = create_resume_graph(
        skills=["python", "machine learning", "communication"],
        evaluate_experience=True,
        evaluate_culture=True,
        evaluate_jd=True
    )

    # OPTIONAL: if you stored files under a date folder like "2025-11-26",
    # put that here. If not, leave it as "" to scan the root of the bucket.
    supabase_folder = "2025-11-26"  # e.g. "" or "2025-11-26"

    # 2. List resumes from Supabase
    objects = list_resumes_in_supabase(folder=supabase_folder)
    print(f"[INFO] Found {len(objects)} objects in Supabase folder '{supabase_folder or '/'}'")

    results = []

    for obj in objects:
        name = obj.get("name")
        if not name:
            continue

        # only care about PDFs
        if not name.lower().endswith(".pdf"):
            continue

        # full path inside the bucket
        storage_path = f"{supabase_folder}/{name}" if supabase_folder else name
        print(f"\n[INFO] Processing Supabase file: {storage_path}")

        # 3. Download to a temp local path, because your graph expects a file path
        local_resume_path = download_resume_from_supabase(
            storage_path,
            local_dir="./temp_resumes"
        )
        print(f"  [DOWNLOADED] -> {local_resume_path}")

        # 4. Build the initial state just like you did before
        initial_state = {
            "resume_path": local_resume_path,
            "job_description": "Looking for a backend engineer with ML + Python experience.",
            "skills_required": ["python", "machine learning", "communication"],
            "agent_outputs": {}
        }

        # 5. Run the LangGraph pipeline
        result = graph.invoke(initial_state)

        final_score = result.get("final_score", 0)
        breakdown = result.get("final_breakdown", {})

        print("  FINAL SCORE:", final_score)
        print("  BREAKDOWN:", breakdown)

        results.append({
            "storage_path": storage_path,
            "local_path": local_resume_path,
            "final_score": final_score,
            "final_breakdown": breakdown,
        })

    # 6. (Optional) Sort by score and show summary
    if results:
        results_sorted = sorted(results, key=lambda x: x["final_score"], reverse=True)

        print("\n=== SUMMARY (sorted by score) ===")
        for r in results_sorted:
            print(f"\nResume: {r['storage_path']}")
            print(f"  Local: {r['local_path']}")
            print(f"  Score: {r['final_score']}")
            print(f"  Breakdown: {r['final_breakdown']}")
    else:
        print("\n[INFO] No PDF resumes found in Supabase to analyze.")

