import os
import jwt
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")


def verify_token(auth_header: str):
    if not auth_header:
        raise Exception("Missing Authorization header")

    token = auth_header.replace("Bearer ", "")

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload["sub"]
    except Exception:
        raise Exception("Invalid or expired JWT")
