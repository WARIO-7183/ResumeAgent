# supabase_client.py
import os
from supabase import create_client, Client
from langsmith import traceable

SUPABASE_URL = ""
SUPABASE_KEY = ""
SUPABASE_BUCKET = "resumes"

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


@traceable(name="list_resumes_supabase")
def list_resumes_in_supabase(folder: str = ""):
    """
    List all objects in the given folder of the 'resumes' bucket.
    """
    path = folder or ""
    result = supabase.storage.from_(SUPABASE_BUCKET).list(path=path)
    return result


@traceable(name="download_resume_supabase")
def download_resume_from_supabase(storage_path: str, local_dir: str = "./temp_resumes") -> str:
    """
    Download a single file from Supabase to local disk and return the local path.
    """
    os.makedirs(local_dir, exist_ok=True)
    file_name = os.path.basename(storage_path)
    local_path = os.path.join(local_dir, file_name)

    data = supabase.storage.from_(SUPABASE_BUCKET).download(storage_path)

    with open(local_path, "wb") as f:
        f.write(data)

    return local_path


@traceable(name="upload_resume_supabase")
def upload_resume_bytes_to_supabase(pdf_bytes: bytes, filename: str, folder: str = "") -> str:
    """
    Upload PDF bytes directly to Supabase storage.
    Returns the storage path.
    """
    storage_path = f"{folder}/{filename}" if folder else filename
    
    supabase.storage.from_(SUPABASE_BUCKET).upload(
        path=storage_path,
        file=pdf_bytes,
        file_options={"content-type": "application/pdf"}
    )
    
    return storage_path