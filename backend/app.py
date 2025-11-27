from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
import tempfile
from datetime import datetime

# Add parent directory to path to import existing modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase_client import (
    supabase, 
    SUPABASE_BUCKET, 
    list_resumes_in_supabase, 
    download_resume_from_supabase,
    upload_resume_bytes_to_supabase
)
from langgraph_pipeline import create_resume_graph

app = Flask(__name__)
CORS(app)

# Create the evaluation graph once (reused for all requests)
evaluation_graph = None

def get_evaluation_graph(skills=None, job_description=None):
    """Get or create the evaluation graph with specified parameters."""
    global evaluation_graph
    if skills is None:
        skills = ["python", "machine learning", "communication"]
    
    evaluation_graph = create_resume_graph(
        skills=skills,
        evaluate_experience=True,
        evaluate_culture=True,
        evaluate_jd=bool(job_description)
    )
    return evaluation_graph


@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"})


@app.route('/api/resumes', methods=['GET'])
def list_resumes():
    """List all resumes from Supabase storage."""
    try:
        folder = request.args.get('folder', '')
        
        # Get list of files from Supabase
        objects = list_resumes_in_supabase(folder=folder)
        
        resumes = []
        for obj in objects:
            name = obj.get('name', '')
            if name and name.lower().endswith('.pdf'):
                # Build full path
                storage_path = f"{folder}/{name}" if folder else name
                resumes.append({
                    'name': name,
                    'storage_path': storage_path,
                    'created_at': obj.get('created_at', ''),
                    'size': obj.get('metadata', {}).get('size', 0) if obj.get('metadata') else 0
                })
        
        return jsonify({
            "success": True,
            "resumes": resumes,
            "count": len(resumes)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/folders', methods=['GET'])
def list_folders():
    """List all date folders in Supabase storage."""
    try:
        objects = supabase.storage.from_(SUPABASE_BUCKET).list(path="")
        
        folders = []
        for obj in objects:
            name = obj.get('name', '')
            # Folders typically don't have file extensions
            if name and '.' not in name:
                folders.append(name)
        
        return jsonify({
            "success": True,
            "folders": sorted(folders, reverse=True)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/upload', methods=['POST'])
def upload_resume():
    """Upload a resume directly to Supabase."""
    try:
        if 'file' not in request.files:
            return jsonify({"success": False, "error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"success": False, "error": "No file selected"}), 400
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({"success": False, "error": "Only PDF files are allowed"}), 400
        
        # Read file bytes
        pdf_bytes = file.read()
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        new_filename = f"{timestamp}_{file.filename.replace(' ', '_')}"
        folder = datetime.now().strftime("%Y-%m-%d")
        
        # Upload to Supabase
        storage_path = upload_resume_bytes_to_supabase(
            pdf_bytes,
            filename=new_filename,
            folder=folder
        )
        
        return jsonify({
            "success": True,
            "storage_path": storage_path,
            "filename": new_filename
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/scan', methods=['POST'])
def scan_resumes():
    """Scan one or more resumes and return evaluation results."""
    try:
        data = request.json
        storage_paths = data.get('storage_paths', [])
        job_description = data.get('job_description', 'Looking for a skilled professional.')
        skills = data.get('skills', ['python', 'machine learning', 'communication'])
        
        if not storage_paths:
            return jsonify({"success": False, "error": "No resumes selected"}), 400
        
        # Get evaluation graph
        graph = get_evaluation_graph(skills=skills, job_description=job_description)
        
        results = []
        
        for storage_path in storage_paths:
            try:
                # Download resume to temp location
                local_path = download_resume_from_supabase(
                    storage_path,
                    local_dir=tempfile.gettempdir()
                )
                
                # Build initial state
                initial_state = {
                    "resume_path": local_path,
                    "job_description": job_description,
                    "skills_required": skills,
                    "agent_outputs": {}
                }
                
                # Run evaluation
                result = graph.invoke(initial_state)
                
                final_score = result.get("final_score", 0)
                breakdown = result.get("final_breakdown", {})
                agent_outputs = result.get("agent_outputs", {})
                
                results.append({
                    "storage_path": storage_path,
                    "filename": os.path.basename(storage_path),
                    "final_score": final_score,
                    "breakdown": breakdown,
                    "details": agent_outputs,
                    "success": True
                })
                
                # Cleanup temp file
                if os.path.exists(local_path):
                    os.remove(local_path)
                    
            except Exception as e:
                results.append({
                    "storage_path": storage_path,
                    "filename": os.path.basename(storage_path),
                    "error": str(e),
                    "success": False
                })
        
        # Sort by score
        results = sorted(results, key=lambda x: x.get('final_score', 0), reverse=True)
        
        return jsonify({
            "success": True,
            "results": results,
            "total_scanned": len(results)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/scan-upload', methods=['POST'])
def scan_uploaded_resume():
    """Upload and immediately scan a resume."""
    try:
        if 'file' not in request.files:
            return jsonify({"success": False, "error": "No file provided"}), 400
        
        file = request.files['file']
        job_description = request.form.get('job_description', 'Looking for a skilled professional.')
        skills_str = request.form.get('skills', 'python,machine learning,communication')
        skills = [s.strip() for s in skills_str.split(',')]
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({"success": False, "error": "Only PDF files are allowed"}), 400
        
        # Save to temp file
        temp_path = os.path.join(tempfile.gettempdir(), file.filename)
        file.save(temp_path)
        
        # Get evaluation graph
        graph = get_evaluation_graph(skills=skills, job_description=job_description)
        
        # Build initial state
        initial_state = {
            "resume_path": temp_path,
            "job_description": job_description,
            "skills_required": skills,
            "agent_outputs": {}
        }
        
        # Run evaluation
        result = graph.invoke(initial_state)
        
        final_score = result.get("final_score", 0)
        breakdown = result.get("final_breakdown", {})
        agent_outputs = result.get("agent_outputs", {})
        
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return jsonify({
            "success": True,
            "filename": file.filename,
            "final_score": final_score,
            "breakdown": breakdown,
            "details": agent_outputs
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)

