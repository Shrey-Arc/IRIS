"""
Authentication utilities for IRIS
Handles JWT verification and user profile management
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client
from typing import Optional, Dict

load_dotenv()

# Supabase client initialization
SUPABASE_URL = os.getenv("SUPABASE_URL")
SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if not all([SUPABASE_URL, SERVICE_KEY]):
    raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in environment")

supabase: Client = create_client(SUPABASE_URL, SERVICE_KEY)

def verify_token(auth_header: Optional[str]) -> str:
    """
    Verify JWT token from Authorization header
    
    Args:
        auth_header: Authorization header value (Bearer <token>)
        
    Returns:
        User ID (uuid) from the token
        
    Raises:
        Exception: If token is invalid or missing
    """
    if not auth_header:
        raise Exception("Missing Authorization header")
    
    # Extract token from "Bearer <token>"
    token = auth_header.replace("Bearer ", "").strip()
    
    if not token:
        raise Exception("Empty token")
    
    try:
        # Use Supabase's built-in auth verification
        response = supabase.auth.get_user(token)
        
        if not response or not response.user:
            raise Exception("Invalid token: User not found")
        
        user_id = response.user.id
        
        # Ensure user profile exists
        ensure_user_profile(user_id, response.user.email)
        
        return user_id
        
    except Exception as e:
        raise Exception(f"Token verification failed: {str(e)}")

def ensure_user_profile(user_id: str, email: Optional[str] = None) -> None:
    """
    Ensure user has a profile entry in the profiles table
    Creates one if it doesn't exist
    
    Args:
        user_id: User's UUID
        email: User's email (optional)
    """
    try:
        # Check if profile exists
        result = supabase.table("profiles").select("id").eq("id", user_id).execute()
        
        if not result.data:
            # Create profile
            profile_data = {
                "id": user_id,
                "remember_me": False  # Default to false for security
            }
            
            if email:
                profile_data["email"] = email
            
            supabase.table("profiles").insert(profile_data).execute()
            
    except Exception as e:
        # Profile might already exist due to race condition - ignore
        pass

def get_user_profile(user_id: str) -> Dict:
    """
    Get user profile data
    
    Args:
        user_id: User's UUID
        
    Returns:
        Profile dictionary
    """
    result = supabase.table("profiles").select("*").eq("id", user_id).execute()
    
    if not result.data:
        raise Exception("Profile not found")
    
    return result.data[0]

def update_user_profile(user_id: str, updates: Dict) -> Dict:
    """
    Update user profile
    
    Args:
        user_id: User's UUID
        updates: Dictionary of fields to update
        
    Returns:
        Updated profile dictionary
    """
    result = supabase.table("profiles").update(updates).eq("id", user_id).execute()
    
    if not result.data:
        raise Exception("Profile update failed")
    
    return result.data[0]

def get_user_remember_me(user_id: str) -> bool:
    """
    Get user's remember_me preference
    
    Args:
        user_id: User's UUID
        
    Returns:
        remember_me boolean value
    """
    try:
        profile = get_user_profile(user_id)
        return profile.get("remember_me", False)
    except:
        return False  # Default to false for safety