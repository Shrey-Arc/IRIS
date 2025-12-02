import os
import hashlib
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)


def generate_and_upload_dossier(document_id, user_id):
    analysis = supabase.table("analyses").select("*").eq("document_id", document_id).execute().data[0]

    content = f"""
    IRIS DOSSIER

    Document ID: {document_id}
    User ID: {user_id}

    Risk Analysis:
    {analysis['risk']}

    Compliance Output:
    {analysis['compliance']}

    Cross Verification:
    {analysis['crossverify']}
    """

    filename = f"{document_id}_dossier.txt"
    with open(filename, "w") as f:
        f.write(content)

    data = open(filename, "rb").read()
    sha256 = hashlib.sha256(data).hexdigest()

    path = f"{user_id}/{filename}"

    supabase.storage.from_("dossiers").upload(path, data)

    signed = supabase.storage.from_("dossiers").create_signed_url(path, 3600)

    supabase.table("dossiers").insert({
        "document_id": document_id,
        "user_id": user_id,
        "dossier_url": signed["signedURL"],
        "sha256": sha256
    }).execute()

    return signed["signedURL"], sha256
