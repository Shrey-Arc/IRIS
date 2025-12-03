"""
Storage utilities for IRIS
Handles Supabase Storage operations for documents, heatmaps, and dossiers
"""

import os
import hashlib
from typing import Tuple, List, Optional
from dotenv import load_dotenv
from supabase import create_client, Client
from fastapi import UploadFile

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase: Client = create_client(SUPABASE_URL, SERVICE_KEY)

async def upload_document_to_supabase(file: UploadFile, user_id: str) -> Tuple[str, str]:
    """
    Upload document to Supabase Storage and create database entry
    
    Args:
        file: UploadFile object from FastAPI
        user_id: User's UUID
        
    Returns:
        Tuple of (document_id, storage_path)
    """
    # Read file data
    data = await file.read()
    
    # Calculate SHA256 hash
    sha256 = hashlib.sha256(data).hexdigest()
    
    # Create storage path: user_id/documents/hash_filename
    storage_path = f"{user_id}/documents/{sha256}_{file.filename}"
    
    try:
        # Upload to Supabase Storage
        supabase.storage.from_("documents").upload(
            path=storage_path,
            file=data,
            file_options={"content-type": "application/pdf"}
        )
    except Exception as e:
        # If file already exists, that's okay
        if "duplicate" not in str(e).lower() and "already exists" not in str(e).lower():
            raise Exception(f"Storage upload failed: {str(e)}")
    
    # Create database entry
    result = supabase.table("documents").insert({
        "user_id": user_id,
        "filename": file.filename,
        "storage_path": storage_path,
        "sha256": sha256,
        "status": "processing"  # Initial status
    }).execute()
    
    if not result.data:
        raise Exception("Failed to create document record")
    
    document_id = result.data[0]["id"]
    
    return document_id, storage_path

def upload_bytes_to_storage(
    bucket: str, 
    path: str, 
    data: bytes, 
    content_type: str = "application/octet-stream"
) -> str:
    """
    Upload raw bytes to Supabase Storage
    
    Args:
        bucket: Storage bucket name
        path: Storage path
        data: Bytes to upload
        content_type: MIME type
        
    Returns:
        Storage path
    """
    try:
        supabase.storage.from_(bucket).upload(
            path=path,
            file=data,
            file_options={"content-type": content_type}
        )
        return path
    except Exception as e:
        if "duplicate" not in str(e).lower() and "already exists" not in str(e).lower():
            raise Exception(f"Storage upload failed: {str(e)}")
        return path

def create_signed_url_for_path(
    bucket: str, 
    path: str, 
    expires: int = 3600
) -> str:
    """
    Create a signed URL for accessing private storage
    
    Args:
        bucket: Storage bucket name
        path: Storage path
        expires: URL expiration time in seconds (default 1 hour)
        
    Returns:
        Signed URL string
    """
    try:
        result = supabase.storage.from_(bucket).create_signed_url(path, expires)
        
        if isinstance(result, dict) and 'signedURL' in result:
            return result['signedURL']
        elif isinstance(result, dict) and 'signed_url' in result:
            return result['signed_url']
        else:
            # Fallback to public URL if signing fails
            return f"{SUPABASE_URL}/storage/v1/object/public/{bucket}/{path}"
            
    except Exception as e:
        raise Exception(f"Failed to create signed URL: {str(e)}")

def download_from_storage(bucket: str, path: str) -> bytes:
    """
    Download file from Supabase Storage
    
    Args:
        bucket: Storage bucket name
        path: Storage path
        
    Returns:
        File data as bytes
    """
    try:
        data = supabase.storage.from_(bucket).download(path)
        return data
    except Exception as e:
        raise Exception(f"Storage download failed: {str(e)}")

def remove_storage_paths(bucket: str, paths: List[str]) -> None:
    """
    Remove multiple files from storage
    
    Args:
        bucket: Storage bucket name
        paths: List of storage paths to remove
    """
    if not paths:
        return
    
    try:
        supabase.storage.from_(bucket).remove(paths)
    except Exception as e:
        # Log but don't fail - files might already be deleted
        print(f"Warning: Failed to remove some files from {bucket}: {str(e)}")

def get_storage_path_for_document(document_id: str) -> Optional[str]:
    """
    Get storage path for a document
    
    Args:
        document_id: Document UUID
        
    Returns:
        Storage path or None
    """
    result = supabase.table("documents").select("storage_path").eq("id", document_id).execute()
    
    if result.data:
        return result.data[0].get("storage_path")
    
    return None

def list_user_storage_paths(user_id: str, bucket: str) -> List[str]:
    """
    List all storage paths for a user in a bucket
    
    Args:
        user_id: User UUID
        bucket: Storage bucket name
        
    Returns:
        List of storage paths
    """
    try:
        # List files in user's folder
        result = supabase.storage.from_(bucket).list(f"{user_id}/")
        
        if result:
            return [f"{user_id}/{item['name']}" for item in result]
        
        return []
    except:
        return []