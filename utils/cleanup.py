"""
Cleanup utilities for IRIS
Handles user data deletion based on remember_me preference
"""

import os
from typing import List
from dotenv import load_dotenv
from supabase import create_client, Client
from .auth import get_user_remember_me
from .audit import log_action

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase: Client = create_client(SUPABASE_URL, SERVICE_KEY)

def delete_user_data_on_logout(user_id: str) -> bool:
    """
    Delete user data on logout if remember_me is False
    
    Args:
        user_id: User UUID
        
    Returns:
        True if data was deleted, False if kept
    """
    # Check remember_me preference
    remember_me = get_user_remember_me(user_id)
    
    if remember_me:
        print(f"[Cleanup] User {user_id} has remember_me=True, keeping data")
        return False
    
    print(f"[Cleanup] User {user_id} has remember_me=False, deleting data")
    
    try:
        # 1. Get all document storage paths
        docs = supabase.table("documents").select("storage_path, id").eq("user_id", user_id).execute()
        doc_paths = [d["storage_path"] for d in docs.data] if docs.data else []
        doc_ids = [d["id"] for d in docs.data] if docs.data else []
        
        # 2. Get all heatmap storage paths
        heatmaps = supabase.table("heatmaps").select("heatmap_path").eq("user_id", user_id).execute()
        heatmap_paths = [h["heatmap_path"] for h in heatmaps.data] if heatmaps.data else []
        
        # 3. Get all dossier paths (extract from URL or get from separate column if stored)
        dossiers = supabase.table("dossiers").select("id").eq("user_id", user_id).execute()
        dossier_ids = [d["id"] for d in dossiers.data] if dossiers.data else []
        
        # Construct dossier paths (format: user_id/dossiers/document_id_dossier.zip)
        dossier_paths = []
        for doc_id in doc_ids:
            dossier_paths.append(f"{user_id}/dossiers/{doc_id}_dossier.zip")
        
        # 4. Delete from storage buckets
        if doc_paths:
            try:
                supabase.storage.from_("documents").remove(doc_paths)
                print(f"[Cleanup] Deleted {len(doc_paths)} documents from storage")
            except Exception as e:
                print(f"[Cleanup] Warning: Failed to delete documents: {e}")
        
        if heatmap_paths:
            try:
                supabase.storage.from_("heatmaps").remove(heatmap_paths)
                print(f"[Cleanup] Deleted {len(heatmap_paths)} heatmaps from storage")
            except Exception as e:
                print(f"[Cleanup] Warning: Failed to delete heatmaps: {e}")
        
        if dossier_paths:
            try:
                supabase.storage.from_("dossiers").remove(dossier_paths)
                print(f"[Cleanup] Deleted {len(dossier_paths)} dossiers from storage")
            except Exception as e:
                print(f"[Cleanup] Warning: Failed to delete dossiers: {e}")
        
        # 5. Delete database records (order matters due to foreign keys)
        # Note: Blockchain certificates are kept immutable as per spec
        
        # Delete extracted texts
        supabase.table("extracted_texts").delete().eq("user_id", user_id).execute()
        print(f"[Cleanup] Deleted extracted_texts records")
        
        # Delete heatmaps
        supabase.table("heatmaps").delete().eq("user_id", user_id).execute()
        print(f"[Cleanup] Deleted heatmaps records")
        
        # Delete analyses
        supabase.table("analyses").delete().eq("user_id", user_id).execute()
        print(f"[Cleanup] Deleted analyses records")
        
        # Delete dossiers
        supabase.table("dossiers").delete().eq("user_id", user_id).execute()
        print(f"[Cleanup] Deleted dossiers records")
        
        # Delete documents
        supabase.table("documents").delete().eq("user_id", user_id).execute()
        print(f"[Cleanup] Deleted documents records")
        
        # 6. Keep profile but reset some fields (optional)
        supabase.table("profiles").update({
            "remember_me": False
        }).eq("id", user_id).execute()
        
        # 7. Log the cleanup action
        log_action(user_id, "delete_user_data_on_logout", "multiple", None, {
            "documents_deleted": len(doc_paths),
            "heatmaps_deleted": len(heatmap_paths),
            "dossiers_deleted": len(dossier_paths)
        })
        
        print(f"[Cleanup] ✓ Successfully deleted all data for user {user_id}")
        return True
        
    except Exception as e:
        print(f"[Cleanup] ✗ Error during cleanup: {str(e)}")
        # Log error but don't fail logout
        try:
            log_action(user_id, "cleanup_error", "multiple", None, {"error": str(e)})
        except:
            pass
        return False

def delete_document_cascade(document_id: str, user_id: str) -> None:
    """
    Delete a document and all related data
    
    Args:
        document_id: Document UUID
        user_id: User UUID (for verification)
    """
    # Verify ownership
    doc = supabase.table("documents").select("storage_path, user_id").eq("id", document_id).execute()
    
    if not doc.data:
        raise Exception("Document not found")
    
    if doc.data[0]["user_id"] != user_id:
        raise Exception("Unauthorized")
    
    storage_path = doc.data[0]["storage_path"]
    
    # Delete storage
    if storage_path:
        try:
            supabase.storage.from_("documents").remove([storage_path])
        except Exception as e:
            print(f"Warning: Failed to delete document from storage: {e}")
    
    # Delete related heatmaps (get analysis_ids first)
    analyses = supabase.table("analyses").select("id").eq("document_id", document_id).execute()
    analysis_ids = [a["id"] for a in analyses.data] if analyses.data else []
    
    if analysis_ids:
        heatmaps = supabase.table("heatmaps").select("heatmap_path").in_("analysis_id", analysis_ids).execute()
        heatmap_paths = [h["heatmap_path"] for h in heatmaps.data] if heatmaps.data else []
        
        if heatmap_paths:
            try:
                supabase.storage.from_("heatmaps").remove(heatmap_paths)
            except Exception as e:
                print(f"Warning: Failed to delete heatmaps: {e}")
        
        supabase.table("heatmaps").delete().in_("analysis_id", analysis_ids).execute()
    
    # Delete related dossiers
    dossiers = supabase.table("dossiers").select("id").eq("document_id", document_id).execute()
    if dossiers.data:
        dossier_path = f"{user_id}/dossiers/{document_id}_dossier.zip"
        try:
            supabase.storage.from_("dossiers").remove([dossier_path])
        except Exception as e:
            print(f"Warning: Failed to delete dossier: {e}")
        
        # Note: Keep blockchain certificates (immutable)
        supabase.table("dossiers").delete().eq("document_id", document_id).execute()
    
    # Delete database records
    supabase.table("extracted_texts").delete().eq("document_id", document_id).execute()
    supabase.table("analyses").delete().eq("document_id", document_id).execute()
    supabase.table("documents").delete().eq("id", document_id).execute()
    
    log_action(user_id, "delete_document_cascade", "documents", document_id)

def cleanup_failed_uploads(user_id: str) -> int:
    """
    Clean up documents that failed to process
    
    Args:
        user_id: User UUID
        
    Returns:
        Number of documents cleaned
    """
    # Get failed documents older than 1 hour
    failed_docs = supabase.table("documents").select("id, storage_path").eq(
        "user_id", user_id
    ).eq("status", "failed").execute()
    
    count = 0
    for doc in failed_docs.data if failed_docs.data else []:
        try:
            delete_document_cascade(doc["id"], user_id)
            count += 1
        except:
            pass
    
    return count