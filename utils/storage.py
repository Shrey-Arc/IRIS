import os
import hashlib
import pdfplumber
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)


async def upload_document_to_supabase(file, user_id):
    data = await file.read()
    sha256 = hashlib.sha256(data).hexdigest()

    path = f"{user_id}/{file.filename}"

    # upload to storage bucket "documents"
    supabase.storage.from_("documents").upload(path, data)

    # save metadata in documents table
    result = supabase.table("documents").insert({
        "user_id": user_id,
        "filename": file.filename,
        "storage_path": path,
        "sha256": sha256
    }).execute()

    return result.data[0]["id"]


def extract_pdf_text(storage_path: str):
    file_data = supabase.storage.from_("documents").download(storage_path)

    with open("temp.pdf", "wb") as f:
        f.write(file_data)

    text = ""
    with pdfplumber.open("temp.pdf") as pdf:
        for page in pdf.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"

    return text
