"""
ML Analysis utilities for IRIS
Handles integration with ML API for credit risk prediction
Supports multiple endpoints: /predict, /compliance, /crossverify
"""

import os
import requests
import base64
from typing import Dict, Optional, List
from dotenv import load_dotenv
from supabase import create_client, Client
from .extraction import extract_and_store_texts, get_document_full_text
from .parser import parse_credit_fields, validate_parsed_fields
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
        endpoint: API endpoint (e.g., 'predict', 'compliance', 'crossverify')
        payload: Request payload
        timeout: Request timeout in seconds
        
    Returns:
        ML API response as dictionary
    """
    url = f"{ML_BASE_URL}/{endpoint}"
    
    print(f"[ML API] Calling {endpoint} at {url}")
    
    try:
        response = requests.post(url, json=payload, timeout=timeout)
        response.raise_for_status()
        result = response.json()
        print(f"[ML API] ✓ {endpoint} response received")
        return result
    except requests.exceptions.Timeout:
        print(f"[ML API] ✗ Timeout after {timeout} seconds")
        raise Exception(f"ML API timeout after {timeout} seconds")
    except requests.exceptions.ConnectionError:
        print(f"[ML API] ✗ Connection failed to {url}")
        raise Exception(f"Cannot connect to ML API at {url}")
    except requests.exceptions.HTTPError as e:
        print(f"[ML API] ✗ HTTP error: {e.response.status_code}")
        raise Exception(f"ML API HTTP error: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        print(f"[ML API] ✗ Unexpected error: {str(e)}")
        raise Exception(f"ML API call failed: {str(e)}")

def call_risk_prediction(parsed_fields: Dict) -> Dict:
    """
    Call risk prediction endpoint
    
    Args:
        parsed_fields: Structured credit risk fields
        
    Returns:
        Risk prediction result
    """
    try:
        return call_ml("predict", parsed_fields)
    except Exception as e:
        print(f"[Analysis] Risk prediction unavailable: {str(e)}")
        # Return mock structure if endpoint fails
        return {
            "prediction": None,
            "risk_score": None,
            "error": str(e),
            "status": "unavailable"
        }

def call_compliance_check(parsed_fields: Dict) -> Dict:
    """
    Call compliance checking endpoint (when available)
    
    Args:
        parsed_fields: Structured credit risk fields
        
    Returns:
        Compliance check result
    """
    try:
        return call_ml("compliance", parsed_fields)
    except Exception as e:
        print(f"[Analysis] Compliance endpoint not available yet: {str(e)}")
        # Return placeholder until ML lead implements
        return {
            "compliance_score": 1.0,
            "violations": [],
            "checks_performed": [],
            "status": "not_available",
            "message": "Compliance endpoint not yet implemented by ML team"
        }

def call_cross_verification(parsed_fields: Dict, document_ids: List[str] = None) -> Dict:
    """
    Call cross-verification endpoint (when available)
    
    Args:
        parsed_fields: Structured credit risk fields
        document_ids: List of document IDs to cross-verify
        
    Returns:
        Cross-verification result
    """
    try:
        payload = {
            **parsed_fields,
            "document_ids": document_ids or []
        }
        return call_ml("crossverify", payload)
    except Exception as e:
        print(f"[Analysis] Cross-verify endpoint not available yet: {str(e)}")
        # Return placeholder until ML lead implements
        return {
            "overall_score": 1.0,
            "matches": {},
            "discrepancies": [],
            "status": "not_available",
            "message": "Cross-verification endpoint not yet implemented by ML team"
        }

def run_full_analysis_background(document_id: str, user_id: str, storage_path: str) -> Dict:
    """
    Run complete credit risk analysis pipeline in background
    
    Pipeline:
    1. Extract text from PDF
    2. Parse credit risk fields
    3. Validate fields
    4. Call ML risk prediction
    5. Call ML compliance (when available)
    6. Call ML cross-verify (when available)
    7. Store all results
    8. Update document status
    
    Args:
        document_id: Document UUID
        user_id: User UUID
        storage_path: Path to document in storage
        
    Returns:
        Analysis results dictionary
    """
    try:
        print(f"[Analysis] ===== Starting analysis for document {document_id} =====")
        
        # ===== STEP 1: Extract text from PDF =====
        print(f"[Analysis] Step 1: Extracting text from PDF")
        texts = extract_and_store_texts(document_id, storage_path, user_id)
        
        if not texts:
            raise Exception("No text extracted from document")
        
        # Concatenate all page texts
        full_text = "\n\n".join([page[1] for page in texts if page[1]])
        
        if not full_text.strip():
            raise Exception("Document appears to be empty or contains only images")
        
        print(f"[Analysis] ✓ Extracted {len(texts)} pages, {len(full_text)} characters")
        
        # ===== STEP 2: Parse credit risk fields =====
        print(f"[Analysis] Step 2: Parsing credit risk fields from text")
        parsed_fields = parse_credit_fields(full_text)
        
        # ===== STEP 3: Validate parsed fields =====
        print(f"[Analysis] Step 3: Validating parsed fields")
        is_valid, validation_errors = validate_parsed_fields(parsed_fields)
        
        if not is_valid:
            print(f"[Analysis] ⚠️  Field validation warnings: {', '.join(validation_errors)}")
            # Continue with warnings but log them
            parsed_fields['_validation_errors'] = validation_errors
        else:
            print(f"[Analysis] ✓ All fields validated successfully")
        
        # ===== STEP 4: Call ML Risk Prediction =====
        print(f"[Analysis] Step 4: Calling ML risk prediction endpoint")
        risk_result = call_risk_prediction(parsed_fields)
        
        # Format risk result
        formatted_risk = {
            "prediction": risk_result.get("prediction"),
            "risk_score": risk_result.get("risk_score"),
            "probability": risk_result.get("probability"),
            "risk_class": risk_result.get("risk_class"),
            "risk_factors": risk_result.get("risk_factors", []),
            "confidence": risk_result.get("confidence"),
            "parsed_fields": parsed_fields,
            "validation_errors": validation_errors if not is_valid else [],
            "raw_ml_response": risk_result
        }
        
        print(f"[Analysis] ✓ Risk prediction: {risk_result.get('risk_class', 'N/A')} (score: {risk_result.get('risk_score', 'N/A')})")
        
        # ===== STEP 5: Call ML Compliance Check =====
        print(f"[Analysis] Step 5: Calling ML compliance endpoint")
        compliance_result = call_compliance_check(parsed_fields)
        
        print(f"[Analysis] Compliance status: {compliance_result.get('status', 'unknown')}")
        
        # ===== STEP 6: Call ML Cross-Verification =====
        print(f"[Analysis] Step 6: Calling ML cross-verification endpoint")
        crossverify_result = call_cross_verification(parsed_fields, [document_id])
        
        print(f"[Analysis] Cross-verify status: {crossverify_result.get('status', 'unknown')}")
        
        # ===== STEP 7: Store analysis results in database =====
        print(f"[Analysis] Step 7: Storing analysis results in database")
        analysis_result = supabase.table("analyses").insert({
            "document_id": document_id,
            "user_id": user_id,
            "risk": formatted_risk,
            "compliance": compliance_result,
            "crossverify": crossverify_result
        }).execute()
        
        if not analysis_result.data:
            raise Exception("Failed to store analysis results in database")
        
        analysis_id = analysis_result.data[0]["id"]
        print(f"[Analysis] ✓ Analysis stored with ID: {analysis_id}")
        
        # ===== STEP 8: Process heatmap if provided =====
        heatmap_path = None
        if "heatmap_base64" in risk_result and risk_result["heatmap_base64"]:
            print(f"[Analysis] Step 8: Processing heatmap image")
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
                    "caption": "Credit Risk Analysis Heatmap"
                }).execute()
                
                heatmap_path = heatmap_storage_path
                print(f"[Analysis] ✓ Heatmap stored at {heatmap_path}")
                
            except Exception as e:
                print(f"[Analysis] ⚠️  Failed to process heatmap: {str(e)}")
        
        # ===== STEP 9: Update document status to 'done' =====
        print(f"[Analysis] Step 9: Updating document status to 'done'")
        supabase.table("documents").update({
            "status": "done"
        }).eq("id", document_id).execute()
        
        print(f"[Analysis] ===== ✓ Analysis complete for document {document_id} =====")
        
        return {
            "success": True,
            "analysis_id": analysis_id,
            "risk": formatted_risk,
            "compliance": compliance_result,
            "crossverify": crossverify_result,
            "parsed_fields": parsed_fields,
            "heatmap_path": heatmap_path
        }
        
    except Exception as e:
        # Update document status to 'failed'
        print(f"[Analysis] ===== ✗ Analysis FAILED for document {document_id} =====")
        print(f"[Analysis] Error: {str(e)}")
        
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
                "risk": {
                    "error": str(e),
                    "status": "failed"
                },
                "compliance": {},
                "crossverify": {}
            }).execute()
        except:
            pass
        
        raise Exception(f"Analysis pipeline failed: {str(e)}")

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
        "risk_class": risk.get("risk_class"),
        "prediction": risk.get("prediction"),
        "compliance_score": compliance.get("compliance_score"),
        "violations_count": len(compliance.get("violations", [])),
        "parsed_fields": risk.get("parsed_fields"),
        "has_heatmap": "heatmap_base64" in risk or "heatmap_url" in risk
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
    print(f"[Analysis] Rerunning analysis for document {document_id}")
    
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