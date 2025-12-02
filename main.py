import os
from fastapi import FastAPI, UploadFile, File, Header
from supabase import create_client
from dotenv import load_dotenv
import jwt
import hashlib
import pdfplumber
import requests

load_dotenv()

app = FastAPI()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")  # backend uses service key
)
