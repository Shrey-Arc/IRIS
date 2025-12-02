from fastapi import FastAPI, UploadFile, File, Header
from utils.auth import verify_token
from utils.storage import upload_document_to_supabase
from utils.analysis import run_full_analysis
from utils.dossier import generate_and_upload_dossier
from utils.blockchain import anchor_on_chain

app = FastAPI()


@app.get("/")
def home():
    return {"status": "IRIS backend is running"}


@app.post("/upload")
async def upload(file: UploadFile = File(...), Authorization: str = Header(None)):
    user_id = verify_token(Authorization)
    document_id = await upload_document_to_supabase(file, user_id)
    return {"document_id": document_id}


@app.post("/analyze/{document_id}")
def analyze(document_id: str, Authorization: str = Header(None)):
    user_id = verify_token(Authorization)
    result = run_full_analysis(document_id, user_id)
    return result


@app.post("/dossier/{document_id}")
def dossier(document_id: str, Authorization: str = Header(None)):
    user_id = verify_token(Authorization)
    file_url, sha256 = generate_and_upload_dossier(document_id, user_id)
    return {"dossier_url": file_url, "sha256": sha256}


@app.post("/anchor/{document_id}")
def anchor(document_id: str, Authorization: str = Header(None)):
    user_id = verify_token(Authorization)
    tx_hash = anchor_on_chain(document_id, user_id)
    return {"tx_hash": tx_hash}
