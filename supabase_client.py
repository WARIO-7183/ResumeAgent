# supabase_client.py
import os
from supabase import create_client, Client

SUPABASE_URL = ""
SUPABASE_KEY = "" # service role / secret key
SUPABASE_BUCKET = "resumes"  # make sure this bucket exists in Supabase Storage

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def list_resumes_in_supabase(folder: str = ""):
    """
    List all objects in the given folder of the 'resumes' bucket.
    """
    path = folder or ""
    return supabase.storage.from_(SUPABASE_BUCKET).list(path=path)


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
