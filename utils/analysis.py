"""
ML Analysis utilities for IRIS
Handles integration with ML API for risk, compliance, and cross-verification
"""

import os
import requests
import base64
from typing import Dict, Optional, List
from dotenv import load_dotenv
from supabase import create_client, Client
from .extraction import extract_and_store_texts, get_document_full_text
from .storage import upload_bytes_to_storage

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
ML_BASE_URL = os.getenv("ML_BASE_URL", "http://localhost:5000")

supabase: Client = create_client(SUPABASE_URL, SERVICE_KEY)

def call_ml(endpoint: str, payload: dict, timeout: int = 60) -> dict:
    """
    Call ML API endpoint
    
    Args:
        endpoint: API endpoint (e.g., 'risk', 'compliance')
        payload: Request payload
        timeout: Request timeout in seconds
        
    Returns:
        ML API response as dictionary
    """
    url = f"{ML_BASE_URL}/{endpoint}"
    
    try:
        response = requests.post(url, json=payload, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        raise Exception(f"ML API timeout after {timeout} seconds")
    except requests.exceptions.ConnectionError:
        raise Exception(f"Cannot connect to ML API at {url}")
    except requests.exceptions.HTTPError as e:
        raise Exception(f"ML API HTTP error: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        raise Exception(f"ML API call failed: {str(e)}")

def run_full_analysis_background(document_id: str, user_id: str, storage_path: str) -> Dict:
    """
    Run complete analysis pipeline in background
    Extracts text, calls ML APIs, stores results
    
    Args:
        document_id: Document UUID
        user_id: User UUID
        storage_path: Path to document in storage
        
    Returns:
        Analysis results dictionary
    """
    try:
        # Step 1: Extract text from PDF
        print(f"[Analysis] Extracting text from document {document_id}")
        texts = extract_and_store_texts(document_id, storage_path, user_id)
        
        if not texts:
            raise Exception("No text extracted from document")
        
        # Concatenate all page texts
        full_text = "\n\n".join([page[1] for page in texts if page[1]])
        
        if not full_text.strip():
            raise Exception("Document appears to be empty or contains only images")
        
        print(f"[Analysis] Extracted {len(texts)} pages, {len(full_text)} characters")
        
        # Step 2: Call ML APIs
        print(f"[Analysis] Calling ML API for risk analysis")
        risk_result = call_ml("risk", {
            "text": full_text,
            "document_id": document_id
        })
        
        print(f"[Analysis] Calling ML API for compliance analysis")
        compliance_result = call_ml("compliance", {
            "text": full_text,
            "document_id": document_id
        })
        
        print(f"[Analysis] Calling ML API for cross-verification")
        crossverify_result = call_ml("crossverify", {
            "document_ids": [document_id],
            "text": full_text
        })
        
        # Step 3: Store analysis results
        print(f"[Analysis] Storing analysis results")
        analysis_result = supabase.table("analyses").insert({
            "document_id": document_id,
            "user_id": user_id,
            "risk": risk_result,
            "compliance": compliance_result,
            "crossverify": crossverify_result
        }).execute()
        
        if not analysis_result.data:
            raise Exception("Failed to store analysis results")
        
        analysis_id = analysis_result.data[0]["id"]
        
        # Step 4: Handle heatmap if provided by ML API
        heatmap_path = None
        
        if "heatmap_base64" in risk_result and risk_result["heatmap_base64"]:
            print(f"[Analysis] Processing heatmap image")
            try:
                # Decode base64 image
                heatmap_bytes = base64.b64decode(risk_result["heatmap_base64"])
                
                # Upload to storage
                heatmap_storage_path = f"{user_id}/heatmaps/{document_id}_risk.png"
                upload_bytes_to_storage(
                    "heatmaps", 
                    heatmap_storage_path, 
                    heatmap_bytes,
                    "image/png"
                )
                
                # Store in database
                supabase.table("heatmaps").insert({
                    "analysis_id": analysis_id,
                    "user_id": user_id,
                    "heatmap_path": heatmap_storage_path,
                    "caption": "Risk Analysis Heatmap"
                }).execute()
                
                heatmap_path = heatmap_storage_path
                print(f"[Analysis] Heatmap stored at {heatmap_path}")
                
            except Exception as e:
                print(f"[Analysis] Warning: Failed to process heatmap: {str(e)}")
        
        elif "heatmap_url" in risk_result and risk_result["heatmap_url"]:
            # ML API provided a URL - store reference
            print(f"[Analysis] Using heatmap URL from ML API")
            supabase.table("heatmaps").insert({
                "analysis_id": analysis_id,
                "user_id": user_id,
                "heatmap_path": risk_result["heatmap_url"],
                "caption": "Risk Analysis Heatmap"
            }).execute()
            
            heatmap_path = risk_result["heatmap_url"]
        
        # Step 5: Update document status to 'done'
        print(f"[Analysis] Updating document status to 'done'")
        supabase.table("documents").update({
            "status": "done"
        }).eq("id", document_id).execute()
        
        print(f"[Analysis] ✓ Analysis complete for document {document_id}")
        
        return {
            "success": True,
            "analysis_id": analysis_id,
            "risk": risk_result,
            "compliance": compliance_result,
            "crossverify": crossverify_result,
            "heatmap_path": heatmap_path
        }
        
    except Exception as e:
        # Update document status to 'failed'
        print(f"[Analysis] ✗ Analysis failed for document {document_id}: {str(e)}")
        
        try:
            supabase.table("documents").update({
                "status": "failed"
            }).eq("id", document_id).execute()
        except:
            pass
        
        # Store error in analyses table for debugging
        try:
            supabase.table("analyses").insert({
                "document_id": document_id,
                "user_id": user_id,
                "risk": {"error": str(e)},
                "compliance": {},
                "crossverify": {}
            }).execute()
        except:
            pass
        
        raise Exception(f"Analysis failed: {str(e)}")

def get_risk_score(document_id: str) -> Optional[float]:
    """
    Get risk score for a document
    
    Args:
        document_id: Document UUID
        
    Returns:
        Risk score (0-1) or None
    """
    result = supabase.table("analyses").select("risk").eq("document_id", document_id).execute()
    
    if result.data and result.data[0].get("risk"):
        return result.data[0]["risk"].get("risk_score")
    
    return None

def get_compliance_score(document_id: str) -> Optional[float]:
    """
    Get compliance score for a document
    
    Args:
        document_id: Document UUID
        
    Returns:
        Compliance score (0-1) or None
    """
    result = supabase.table("analyses").select("compliance").eq("document_id", document_id).execute()
    
    if result.data and result.data[0].get("compliance"):
        return result.data[0]["compliance"].get("compliance_score")
    
    return None

def get_analysis_summary(document_id: str) -> Dict:
    """
    Get summary of all analyses for a document
    
    Args:
        document_id: Document UUID
        
    Returns:
        Summary dictionary
    """
    result = supabase.table("analyses").select("*").eq("document_id", document_id).execute()
    
    if not result.data:
        return {
            "has_analysis": False,
            "risk_score": None,
            "compliance_score": None,
            "violations_count": 0
        }
    
    analysis = result.data[0]
    
    risk = analysis.get("risk", {})
    compliance = analysis.get("compliance", {})
    
    return {
        "has_analysis": True,
        "risk_score": risk.get("risk_score"),
        "compliance_score": compliance.get("compliance_score"),
        "violations_count": len(compliance.get("violations", [])),
        "top_risk_factors": risk.get("top_factors", []),
        "has_heatmap": "heatmap_url" in risk or "heatmap_base64" in risk
    }

def rerun_analysis(document_id: str, user_id: str) -> Dict:
    """
    Rerun analysis for an existing document
    
    Args:
        document_id: Document UUID
        user_id: User UUID
        
    Returns:
        Analysis results
    """
    # Get document storage path
    doc = supabase.table("documents").select("storage_path").eq("id", document_id).execute()
    
    if not doc.data:
        raise Exception("Document not found")
    
    storage_path = doc.data[0]["storage_path"]
    
    # Update status to processing
    supabase.table("documents").update({"status": "processing"}).eq("id", document_id).execute()
    
    # Delete old analysis
    supabase.table("analyses").delete().eq("document_id", document_id).execute()
    
    # Delete old extracted texts
    supabase.table("extracted_texts").delete().eq("document_id", document_id).execute()
    
    # Run new analysis
    return run_full_analysis_background(document_id, user_id, storage_path)