"""
Audit logging utilities for IRIS
Tracks all significant user actions
"""

import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase: Client = create_client(SUPABASE_URL, SERVICE_KEY)

def log_action(
    user_id: str,
    action: str,
    target_table: str,
    target_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a user action to audit_logs table
    
    Args:
        user_id: User UUID
        action: Action name (e.g., 'upload', 'delete_document')
        target_table: Table affected (e.g., 'documents', 'analyses')
        target_id: ID of affected record (optional)
        metadata: Additional context data (optional)
    """
    try:
        supabase.table("audit_logs").insert({
            "user_id": user_id,
            "action": action,
            "target_table": target_table,
            "target_id": target_id,
            "metadata": metadata or {}
        }).execute()
        
        print(f"[Audit] {user_id} - {action} on {target_table}")
        
    except Exception as e:
        # Don't fail the operation if audit logging fails
        print(f"[Audit] Warning: Failed to log action: {str(e)}")

def get_user_audit_trail(user_id: str, limit: int = 100) -> list:
    """
    Get audit trail for a user
    
    Args:
        user_id: User UUID
        limit: Maximum number of records to return
        
    Returns:
        List of audit log entries
    """
    result = supabase.table("audit_logs").select("*").eq(
        "user_id", user_id
    ).order("created_at", desc=True).limit(limit).execute()
    
    return result.data if result.data else []

def get_document_audit_trail(document_id: str) -> list:
    """
    Get audit trail for a specific document
    
    Args:
        document_id: Document UUID
        
    Returns:
        List of audit log entries
    """
    result = supabase.table("audit_logs").select("*").eq(
        "target_id", document_id
    ).order("created_at", desc=True).execute()
    
    return result.data if result.data else []

def get_recent_actions(limit: int = 50) -> list:
    """
    Get recent actions across all users (admin function)
    
    Args:
        limit: Maximum number of records
        
    Returns:
        List of recent audit logs
    """
    result = supabase.table("audit_logs").select("*").order(
        "created_at", desc=True
    ).limit(limit).execute()
    
    return result.data if result.data else []