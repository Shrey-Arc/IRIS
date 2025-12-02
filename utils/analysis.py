import os
import requests
from dotenv import load_dotenv
from supabase import create_client
from utils.storage import extract_pdf_text

load_dotenv()

ML_URL = os.getenv("ML_BASE_URL")

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)


def call_ml(model, text):
    response = requests.post(
        f"{ML_URL}/{model}", 
        json={"text": text}
    )
    return response.json()


def run_full_analysis(document_id, user_id):
    doc = supabase.table("documents").select("*").eq("id", document_id).execute().data[0]

    text = extract_pdf_text(doc["storage_path"])

    risk = call_ml("risk", text)
    compliance = call_ml("compliance", text)
    crossverify = call_ml("crossverify", text)

    supabase.table("analyses").insert({
        "document_id": document_id,
        "user_id": user_id,
        "risk": risk,
        "compliance": compliance,
        "crossverify": crossverify
    }).execute()

    return {
        "risk": risk,
        "compliance": compliance,
        "crossverify": crossverify
    }
