"""
Credit field extraction from PDF text
Extracts and classifies structured fields for ML credit risk prediction
"""

import re
from typing import Optional, Dict, Any
from datetime import datetime

def extract_age(text: str) -> Optional[int]:
    """Extract age from text (18-100)"""
    patterns = [
        r'age[:\s]+(\d{2,3})',
        r'(\d{2})\s*years?\s*old',
        r'age[:\s]*(\d{2,3})\s*years?',
        r'dob[:\s]+(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
        r'date\s+of\s+birth[:\s]+(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            if len(match.groups()) == 3:  # DOB format
                year = int(match.group(3))
                if year > 1900:
                    age = datetime.now().year - year
                    if 18 <= age <= 100:
                        return age
            else:
                age = int(match.group(1))
                if 18 <= age <= 100:
                    return age
    
    return None

def extract_gender(text: str) -> Optional[str]:
    """Extract gender (male/female)"""
    text_lower = text.lower()
    
    # Look for explicit gender mentions
    if re.search(r'\bgender[:\s]*(male|m)\b', text_lower):
        return "male"
    elif re.search(r'\bgender[:\s]*(female|f)\b', text_lower):
        return "female"
    
    # Look for titles
    if re.search(r'\b(mr\.|mr|sir)\b', text_lower) and not re.search(r'\b(mrs\.|mrs|ms\.|ms|miss)\b', text_lower):
        return "male"
    elif re.search(r'\b(mrs\.|mrs|ms\.|ms|miss|madam)\b', text_lower):
        return "female"
    
    return None

def classify_job_category(text: str) -> str:
    """Classify job into: unemployed, unskilled, skilled, highly skilled"""
    text_lower = text.lower()
    
    # Check unemployed first
    if re.search(r'\b(unemployed|jobless|not\s+working|no\s+job|not\s+employed)\b', text_lower):
        return "unemployed"
    
    # Highly skilled patterns
    highly_skilled_keywords = [
        'engineer', 'doctor', 'lawyer', 'architect', 'professor', 'surgeon',
        'manager', 'director', 'ceo', 'cfo', 'cto', 'executive', 'vp',
        'consultant', 'analyst', 'scientist', 'researcher', 'specialist',
        'chartered accountant', 'ca', 'mba', 'phd', 'md'
    ]
    
    # Skilled patterns
    skilled_keywords = [
        'technician', 'nurse', 'teacher', 'accountant', 'programmer', 'developer',
        'electrician', 'plumber', 'mechanic', 'carpenter', 'chef', 'cook',
        'officer', 'supervisor', 'coordinator', 'administrator', 'designer',
        'clerk', 'cashier', 'operator', 'driver', 'salesman'
    ]
    
    # Unskilled patterns
    unskilled_keywords = [
        'helper', 'assistant', 'cleaner', 'guard', 'security',
        'laborer', 'labourer', 'worker', 'peon', 'attendant',
        'watchman', 'housekeeping', 'daily wage'
    ]
    
    # Check categories
    for keyword in highly_skilled_keywords:
        if keyword in text_lower:
            return "highly skilled"
    
    for keyword in skilled_keywords:
        if keyword in text_lower:
            return "skilled"
    
    for keyword in unskilled_keywords:
        if keyword in text_lower:
            return "unskilled"
    
    # Look for occupation/job/employment mentions
    if re.search(r'\b(employed|occupation|profession|job|work|working)\b', text_lower):
        return "skilled"  # Default assumption
    
    return "unemployed"

def classify_housing_type(text: str) -> str:
    """Classify housing: free, rent, own"""
    text_lower = text.lower()
    
    # Own patterns
    if re.search(r'\b(own|owned|owner|self[- ]owned|property\s+owner)\b', text_lower):
        return "own"
    
    # Rent patterns
    if re.search(r'\b(rent|rented|rental|tenant|lease|leased|renting)\b', text_lower):
        return "rent"
    
    # Free patterns
    if re.search(r'\b(free|provided|company\s+housing|parents|family\s+house|no\s+rent)\b', text_lower):
        return "free"
    
    # Default
    return "rent"

def classify_savings_level(text: str) -> str:
    """Classify savings: none, little, moderate, quite rich, rich"""
    text_lower = text.lower()
    
    # Try to extract amount first
    amount = extract_account_amount(text_lower, 'saving')
    
    if amount is not None:
        if amount == 0:
            return "none"
        elif amount < 1000:
            return "little"
        elif amount < 10000:
            return "moderate"
        elif amount < 50000:
            return "quite rich"
        else:
            return "rich"
    
    # Pattern matching for explicit mentions
    if re.search(r'saving[s]?[:\s]*(none|no|zero|nil|\b0\b)', text_lower):
        return "none"
    elif re.search(r'saving[s]?[:\s]*(little|small|minimal|low)', text_lower):
        return "little"
    elif re.search(r'saving[s]?[:\s]*(quite\s+rich|very\s+good|substantial|significant)', text_lower):
        return "quite rich"
    elif re.search(r'saving[s]?[:\s]*(rich|high|excellent|strong)', text_lower):
        return "rich"
    elif re.search(r'saving[s]?[:\s]*(moderate|average|medium|fair)', text_lower):
        return "moderate"
    
    # Default
    return "little"

def classify_checking_level(text: str) -> str:
    """Classify checking account: none, little, moderate, rich"""
    text_lower = text.lower()
    
    # Try to extract amount
    amount = extract_account_amount(text_lower, 'checking')
    
    if amount is not None:
        if amount == 0:
            return "none"
        elif amount < 500:
            return "little"
        elif amount < 5000:
            return "moderate"
        else:
            return "rich"
    
    # Pattern matching
    if re.search(r'checking[:\s]*(none|no|zero|nil|\b0\b)', text_lower):
        return "none"
    elif re.search(r'checking[:\s]*(little|small|minimal|low)', text_lower):
        return "little"
    elif re.search(r'checking[:\s]*(rich|high|substantial|significant)', text_lower):
        return "rich"
    elif re.search(r'checking[:\s]*(moderate|average|medium|fair)', text_lower):
        return "moderate"
    
    # Default
    return "little"

def extract_credit_amount(text: str) -> Optional[float]:
    """Extract credit/loan amount"""
    patterns = [
        r'(?:loan|credit)\s*(?:amount|sum)?[:\s]*(?:rs\.?|₹|inr|\$)?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
        r'(?:amount|sum)[:\s]*(?:rs\.?|₹|inr|\$)?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
        r'(?:rs\.?|₹|inr|\$)\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
        r'principal[:\s]*(?:rs\.?|₹|inr|\$)?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            amount_str = match.group(1).replace(',', '')
            amount = float(amount_str)
            if amount > 0:
                return amount
    
    return None

def extract_duration_months(text: str) -> Optional[int]:
    """Extract loan duration in months"""
    
    # Month patterns
    month_patterns = [
        r'duration[:\s]*(\d+)\s*months?',
        r'tenure[:\s]*(\d+)\s*months?',
        r'period[:\s]*(\d+)\s*months?',
        r'term[:\s]*(\d+)\s*months?',
        r'(\d+)\s*months?\s*(?:loan|tenure|period|term)',
    ]
    
    for pattern in month_patterns:
        match = re.search(pattern, text.lower())
        if match:
            months = int(match.group(1))
            if 1 <= months <= 120:  # Reasonable range
                return months
    
    # Year patterns (convert to months)
    year_patterns = [
        r'duration[:\s]*(\d+)\s*years?',
        r'tenure[:\s]*(\d+)\s*years?',
        r'period[:\s]*(\d+)\s*years?',
        r'term[:\s]*(\d+)\s*years?',
    ]
    
    for pattern in year_patterns:
        match = re.search(pattern, text.lower())
        if match:
            years = int(match.group(1))
            if 1 <= years <= 10:
                return years * 12
    
    return None

def classify_loan_purpose(text: str) -> str:
    """Classify loan purpose"""
    text_lower = text.lower()
    
    purposes = {
        "business": ['business', 'enterprise', 'startup', 'commercial', 'shop', 'office'],
        "car": ['car', 'vehicle', 'automobile', 'auto', 'bike', 'motorcycle'],
        "domestic appliances": ['appliance', 'refrigerator', 'fridge', 'washing machine', 'microwave', 'ac', 'air conditioner'],
        "education": ['education', 'study', 'course', 'tuition', 'school', 'college', 'university', 'training'],
        "furniture/equipment": ['furniture', 'equipment', 'furnishing', 'sofa', 'bed', 'table'],
        "radio/TV": ['radio', 'tv', 'television', 'electronics', 'audio', 'video'],
        "repairs": ['repair', 'renovation', 'maintenance', 'fix', 'remodel'],
    }
    
    # Check purpose field explicitly
    purpose_match = re.search(r'purpose[:\s]*([a-zA-Z\s/]+)', text_lower)
    if purpose_match:
        purpose_text = purpose_match.group(1).strip()
        for purpose, keywords in purposes.items():
            for keyword in keywords:
                if keyword in purpose_text:
                    return purpose
    
    # Check entire text
    for purpose, keywords in purposes.items():
        for keyword in keywords:
            if keyword in text_lower:
                return purpose
    
    # Default
    return "vacation/others"

def extract_account_amount(text: str, account_type: str) -> Optional[float]:
    """Helper to extract account balance amounts"""
    patterns = [
        rf'{account_type}[:\s]*(?:balance|account)?[:\s]*(?:rs\.?|₹|inr|\$)?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
        rf'{account_type}[:\s]*(?:a/c|acc)[:\s]*(?:rs\.?|₹|inr|\$)?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            amount_str = match.group(1).replace(',', '')
            return float(amount_str)
    
    return None

def parse_credit_fields(text: str) -> Dict[str, Any]:
    """
    Main function: Extract all credit risk fields from document text
    
    Args:
        text: Full extracted PDF text
        
    Returns:
        Dictionary with all required fields for ML API
    """
    print("[Parser] Starting field extraction from document text")
    
    fields = {
        "age": extract_age(text),
        "gender": extract_gender(text),
        "job": classify_job_category(text),
        "housing": classify_housing_type(text),
        "saving_accounts": classify_savings_level(text),
        "checking_account": classify_checking_level(text),
        "credit_amount": extract_credit_amount(text),
        "duration": extract_duration_months(text),
        "purpose": classify_loan_purpose(text)
    }
    
    # Log extracted fields
    for field, value in fields.items():
        status = "✓" if value is not None else "✗"
        print(f"[Parser] {status} {field}: {value}")
    
    # Check for missing critical fields
    missing = [k for k, v in fields.items() if v is None]
    if missing:
        print(f"[Parser] ⚠️  Warning: Missing fields: {missing}")
    
    return fields

def validate_parsed_fields(fields: Dict[str, Any]) -> tuple[bool, list]:
    """
    Validate extracted fields meet ML API requirements
    
    Returns:
        (is_valid, list_of_errors)
    """
    errors = []
    
    # Age validation
    if fields.get('age') is None:
        errors.append("Age not found in document")
    elif not (18 <= fields['age'] <= 100):
        errors.append(f"Age {fields['age']} out of valid range (18-100)")
    
    # Gender validation
    if fields.get('gender') not in ['male', 'female']:
        errors.append("Gender must be 'male' or 'female'")
    
    # Job validation
    valid_jobs = ['unemployed', 'unskilled', 'skilled', 'highly skilled']
    if fields.get('job') not in valid_jobs:
        errors.append(f"Job '{fields.get('job')}' must be one of {valid_jobs}")
    
    # Housing validation
    valid_housing = ['free', 'rent', 'own']
    if fields.get('housing') not in valid_housing:
        errors.append(f"Housing '{fields.get('housing')}' must be one of {valid_housing}")
    
    # Savings validation
    valid_savings = ['none', 'little', 'moderate', 'quite rich', 'rich']
    if fields.get('saving_accounts') not in valid_savings:
        errors.append(f"Saving accounts must be one of {valid_savings}")
    
    # Checking validation
    valid_checking = ['none', 'little', 'moderate', 'rich']
    if fields.get('checking_account') not in valid_checking:
        errors.append(f"Checking account must be one of {valid_checking}")
    
    # Credit amount validation
    if fields.get('credit_amount') is None:
        errors.append("Credit amount not found in document")
    elif fields['credit_amount'] <= 0:
        errors.append("Credit amount must be positive")
    
    # Duration validation
    if fields.get('duration') is None:
        errors.append("Loan duration not found in document")
    elif fields['duration'] <= 0:
        errors.append("Duration must be positive (in months)")
    
    # Purpose validation
    valid_purposes = [
        'business', 'car', 'domestic appliances', 'education',
        'furniture/equipment', 'radio/TV', 'repairs', 'vacation/others'
    ]
    if fields.get('purpose') not in valid_purposes:
        errors.append(f"Purpose must be one of {valid_purposes}")
    
    is_valid = len(errors) == 0
    
    if is_valid:
        print("[Parser] ✓ All fields validated successfully")
    else:
        print(f"[Parser] ✗ Validation failed: {len(errors)} error(s)")
        for error in errors:
            print(f"[Parser]   - {error}")
    
    return (is_valid, errors)