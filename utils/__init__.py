"""
IRIS Backend Utilities Package
"""

from .auth import verify_token, get_user_profile, supabase
from .storage import upload_document_to_supabase, create_signed_url_for_path
from .extraction import extract_and_store_texts, get_document_full_text
from .analysis import run_full_analysis_background, call_ml
from .dossier import generate_and_upload_dossier
from .cleanup import delete_user_data_on_logout
from .blockchain import anchor_dossier_on_chain
from .audit import log_action

__all__ = [
    'verify_token',
    'get_user_profile',
    'supabase',
    'upload_document_to_supabase',
    'create_signed_url_for_path',
    'extract_and_store_texts',
    'get_document_full_text',
    'run_full_analysis_background',
    'call_ml',
    'generate_and_upload_dossier',
    'delete_user_data_on_logout',
    'anchor_dossier_on_chain',
    'log_action'
]