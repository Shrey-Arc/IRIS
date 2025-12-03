"""
Text extraction utilities for IRIS
Handles PDF text extraction using pdfplumber and OCR fallback
"""

import os
import tempfile
from typing import List, Tuple
from dotenv import load_dotenv
from supabase import create_client, Client
import pdfplumber

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase: Client = create_client(SUPABASE_URL, SERVICE_KEY)

def extract_and_store_texts(
    document_id: str, 
    storage_path: str, 
    user_id: str
) -> List[Tuple[int, str]]:
    """
    Extract text from PDF and store in database
    
    Args:
        document_id: Document UUID
        storage_path: Path to document in storage
        user_id: User UUID
        
    Returns:
        List of tuples (page_number, text)
    """
    # Download document from storage
    try:
        data = supabase.storage.from_("documents").download(storage_path)
    except Exception as e:
        raise Exception(f"Failed to download document: {str(e)}")
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_path = tmp_file.name
        tmp_file.write(data)
    
    texts = []
    
    try:
        # Extract text using pdfplumber
        with pdfplumber.open(tmp_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                try:
                    # Extract text from page
                    text = page.extract_text()
                    
                    if not text:
                        text = ""
                    
                    # Clean text
                    text = text.strip()
                    
                    texts.append((page_num, text))
                    
                    # Store in database
                    supabase.table("extracted_texts").insert({
                        "document_id": document_id,
                        "user_id": user_id,
                        "page_number": page_num,
                        "text": text
                    }).execute()
                    
                except Exception as e:
                    print(f"Warning: Failed to extract text from page {page_num}: {str(e)}")
                    # Continue with other pages
                    texts.append((page_num, ""))
                    
    except Exception as e:
        raise Exception(f"PDF extraction failed: {str(e)}")
    finally:
        # Clean up temporary file
        try:
            os.unlink(tmp_path)
        except:
            pass
    
    return texts

def get_document_full_text(document_id: str) -> str:
    """
    Get concatenated full text of a document
    
    Args:
        document_id: Document UUID
        
    Returns:
        Full text string
    """
    result = supabase.table("extracted_texts").select("page_number, text").eq(
        "document_id", document_id
    ).order("page_number").execute()
    
    if not result.data:
        return ""
    
    # Concatenate all pages
    full_text = "\n\n".join([page["text"] for page in result.data])
    
    return full_text

def get_document_page_text(document_id: str, page_number: int) -> str:
    """
    Get text from a specific page
    
    Args:
        document_id: Document UUID
        page_number: Page number (1-indexed)
        
    Returns:
        Page text
    """
    result = supabase.table("extracted_texts").select("text").eq(
        "document_id", document_id
    ).eq("page_number", page_number).execute()
    
    if not result.data:
        return ""
    
    return result.data[0]["text"]

def get_document_page_count(document_id: str) -> int:
    """
    Get total number of pages in document
    
    Args:
        document_id: Document UUID
        
    Returns:
        Number of pages
    """
    result = supabase.table("extracted_texts").select("page_number").eq(
        "document_id", document_id
    ).execute()
    
    return len(result.data) if result.data else 0

def search_text_in_document(document_id: str, search_term: str) -> List[dict]:
    """
    Search for text within a document
    
    Args:
        document_id: Document UUID
        search_term: Text to search for
        
    Returns:
        List of matches with page numbers
    """
    result = supabase.table("extracted_texts").select("page_number, text").eq(
        "document_id", document_id
    ).execute()
    
    if not result.data:
        return []
    
    matches = []
    search_lower = search_term.lower()
    
    for page in result.data:
        text = page["text"]
        if search_lower in text.lower():
            # Find context around match
            index = text.lower().find(search_lower)
            start = max(0, index - 50)
            end = min(len(text), index + len(search_term) + 50)
            context = text[start:end]
            
            matches.append({
                "page_number": page["page_number"],
                "context": context,
                "full_text": text
            })
    
    return matches