"""
ML API Mock Server for IRIS
Simulates ML endpoints during development
"""

from fastapi import FastAPI
from pydantic import BaseModel
import random
import base64

app = FastAPI(title="IRIS ML Mock API")

class RiskRequest(BaseModel):
    text: str
    document_id: str = None

class ComplianceRequest(BaseModel):
    text: str
    document_id: str = None

class CrossVerifyRequest(BaseModel):
    document_ids: list
    text: str = None

@app.get("/")
def home():
    return {
        "status": "online",
        "service": "IRIS ML Mock API",
        "endpoints": ["/risk", "/compliance", "/crossverify"]
    }

@app.post("/risk")
def analyze_risk(request: RiskRequest):
    """Mock risk analysis endpoint"""
    
    # Generate random but realistic risk score
    risk_score = round(random.uniform(0.3, 0.85), 2)
    
    # Sample risk factors based on score
    all_factors = [
        "Late EMI payments detected",
        "High credit utilization ratio",
        "Multiple credit inquiries",
        "Insufficient income documentation",
        "Employment gap identified",
        "Previous loan default history",
        "Irregular transaction patterns",
        "Low credit history length"
    ]
    
    # Select factors based on risk score
    num_factors = 2 if risk_score < 0.5 else 4 if risk_score < 0.7 else 5
    top_factors = random.sample(all_factors, num_factors)
    
    # Generate explanation
    if risk_score < 0.4:
        explanation = "Financial profile shows strong stability with consistent income and good credit history."
    elif risk_score < 0.7:
        explanation = "Financial profile shows moderate risk due to some credit utilization concerns and payment irregularities."
    else:
        explanation = "Financial profile indicates elevated risk with multiple red flags in credit history and income verification."
    
    # Mock heatmap (small 1x1 pixel PNG in base64 for testing)
    # In real implementation, ML API would return actual heatmap visualization
    mock_heatmap_base64 = None  # Set to None to skip heatmap generation in mock
    
    return {
        "risk_score": risk_score,
        "top_factors": top_factors,
        "explanation": explanation,
        "heatmap_base64": mock_heatmap_base64,
        "heatmap_url": None,
        "confidence": round(random.uniform(0.75, 0.95), 2),
        "model_version": "mock-v1.0"
    }

@app.post("/compliance")
def analyze_compliance(request: ComplianceRequest):
    """Mock compliance analysis endpoint"""
    
    # Generate random compliance score
    compliance_score = round(random.uniform(0.65, 0.95), 2)
    
    # Sample violations (fewer if higher compliance score)
    all_violations = [
        {
            "clause": "RBI KYC 4.2(b)",
            "issue": "Missing current address proof",
            "severity": "medium"
        },
        {
            "clause": "RBI Fair Practice 6.1",
            "issue": "Interest rate disclosure incomplete",
            "severity": "high"
        },
        {
            "clause": "KYC Guidelines 2.1.3",
            "issue": "PAN verification pending",
            "severity": "high"
        },
        {
            "clause": "AML Guidelines 5.2",
            "issue": "Source of funds documentation incomplete",
            "severity": "medium"
        },
        {
            "clause": "PMLA Section 12",
            "issue": "Beneficial ownership not disclosed",
            "severity": "low"
        }
    ]
    
    # Number of violations based on compliance score
    if compliance_score > 0.9:
        violations = []
    elif compliance_score > 0.75:
        violations = random.sample(all_violations, 1)
    else:
        violations = random.sample(all_violations, random.randint(2, 4))
    
    return {
        "compliance_score": compliance_score,
        "violations": violations,
        "total_checks": 25,
        "passed_checks": int(25 * compliance_score),
        "status": "compliant" if compliance_score > 0.8 else "non_compliant",
        "model_version": "mock-v1.0"
    }

@app.post("/crossverify")
def cross_verify(request: CrossVerifyRequest):
    """Mock cross-verification endpoint"""
    
    # Generate random verification results
    fields = ["name", "dob", "pan", "address", "phone", "email"]
    matches = {}
    
    for field in fields:
        rand = random.random()
        if rand < 0.7:
            matches[field] = "match"
        elif rand < 0.85:
            matches[field] = "partial_match"
        else:
            matches[field] = "mismatch"
    
    # Calculate overall score
    match_scores = {
        "match": 1.0,
        "partial_match": 0.5,
        "mismatch": 0.0
    }
    
    total_score = sum(match_scores[status] for status in matches.values())
    overall_score = round(total_score / len(fields), 2)
    
    # Generate discrepancy details
    discrepancies = []
    for field, status in matches.items():
        if status != "match":
            discrepancies.append({
                "field": field,
                "status": status,
                "details": f"{field.upper()} shows {status.replace('_', ' ')}"
            })
    
    return {
        "matches": matches,
        "overall_score": overall_score,
        "discrepancies": discrepancies,
        "confidence": round(random.uniform(0.8, 0.95), 2),
        "documents_compared": len(request.document_ids),
        "model_version": "mock-v1.0"
    }

if __name__ == "__main__":
    import uvicorn
    print("Starting IRIS ML Mock API on http://localhost:5000")
    print("Endpoints available: /risk, /compliance, /crossverify")
    uvicorn.run(app, host="0.0.0.0", port=5000, reload=True)