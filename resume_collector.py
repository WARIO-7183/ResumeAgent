import os
import imaplib
import email
from email.header import decode_header
from datetime import datetime
from supabase_client import upload_resume_bytes_to_supabase

IMAP_HOST = "imap.gmail.com"
EMAIL_USER = ""      
EMAIL_PASS = ""        


def connect_imap():
    mail = imaplib.IMAP4_SSL(IMAP_HOST)
    mail.login(EMAIL_USER, EMAIL_PASS)
    return mail


def _decode_subject(subject_header):
    if not subject_header:
        return ""
    decoded_parts = decode_header(subject_header)
    chunks = []
    for part, enc in decoded_parts:
        if isinstance(part, bytes):
            chunks.append(part.decode(enc or "utf-8", errors="ignore"))
        else:
            chunks.append(part)
    return "".join(chunks)


def subject_contains_resume_or_cv(subject_header):
    subject = _decode_subject(subject_header)
    sl = subject.lower()
    match = ("resume" in sl) or ("cv" in sl)
    return match, subject


def fetch_and_upload_new_resume_emails(debug=True):
    """
    Fetch ONLY new (UNSEEN) emails, extract PDFs,
    upload them directly to Supabase, and return metadata.

    Returns (collected, total_pdfs)

    collected: list of dicts:
    {
        "from_email": ...,
        "subject": ...,
        "supabase_paths": [... list of Supabase storage paths ...]
    }
    """
    mail = connect_imap()
    mail.select("inbox")

    typ, data = mail.search(None, '(UNSEEN)')
    if typ != "OK":
        print("[ERROR] Failed to search inbox.")
        mail.logout()
        return [], 0

    email_ids = data[0].split()
    if debug:
        print(f"[INFO] Found {len(email_ids)} new email(s).")

    collected = []
    total_pdfs = 0

    for eid in email_ids:
        if debug:
            print(f"\n[INFO] Processing email ID={eid.decode()}")

        typ, msg_data = mail.fetch(eid, "(RFC822)")
        if typ != "OK":
            print(f"[WARN] Could not fetch email {eid}")
            continue

        msg = email.message_from_bytes(msg_data[0][1])

        match, subject = subject_contains_resume_or_cv(msg.get("Subject"))
        if debug:
            print(f"  Subject: {subject!r}")
            print(f"  Contains resume/cv? {match}")

        if not match:
            continue

        from_email = email.utils.parseaddr(msg.get("From"))[1]
        supabase_paths = []

        if msg.is_multipart():
            for part in msg.walk():
                cdisp = (part.get("Content-Disposition") or "").lower()
                ctype = part.get_content_type()

                # Treat as resume attachment if attachment or PDF
                if ("attachment" in cdisp) or (ctype == "application/pdf"):
                    orig_filename = part.get_filename() or "resume.pdf"
                    if not orig_filename.lower().endswith(".pdf"):
                        continue

                    pdf_bytes = part.get_payload(decode=True)
                    if not pdf_bytes:
                        continue

                    total_pdfs += 1

                    # build a unique filename for storage (timestamp + original)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                    new_filename = f"{timestamp}_{orig_filename.replace(' ', '_')}"

                    # optional folder by date for organization
                    folder = datetime.now().strftime("%Y-%m-%d")

                    if debug:
                        print(f"  [UPLOAD] {new_filename} -> Supabase folder '{folder}'")

                    storage_path = upload_resume_bytes_to_supabase(
                        pdf_bytes,
                        filename=new_filename,
                        folder=folder,
                    )
                    supabase_paths.append(storage_path)

                    if debug:
                        print(f"  [UPLOADED TO SUPABASE] {storage_path}")

        if supabase_paths:
            collected.append({
                "from_email": from_email,
                "subject": subject,
                "supabase_paths": supabase_paths,
            })
            # Mark as SEEN so we don't process again
            mail.store(eid, '+FLAGS', '\\Seen')

    mail.logout()

    if debug:
        print("\n=== SUMMARY ===")
        print(f"[INFO] Emails with resumes: {len(collected)}")
        print(f"[INFO] Total new PDF resumes uploaded: {total_pdfs}")

    return collected, total_pdfs


if __name__ == "__main__":
    collected, total_pdfs = fetch_and_upload_new_resume_emails(debug=True)
    print("\n[RESULT]")
    print(f"Total PDFs uploaded: {total_pdfs}")
    for item in collected:
        print(item["from_email"], item["subject"], item["supabase_paths"])
