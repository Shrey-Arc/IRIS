"""
Blockchain utilities for IRIS
Handles Sepolia blockchain anchoring via Hardhat/ethers.js
"""

import os
import json
import subprocess
from typing import Tuple
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
HARDHAT_RPC_URL = os.getenv("HARDHAT_RPC_URL", "https://sepolia.infura.io/v3/YOUR_INFURA_KEY")
DEPLOYER_PRIVATE_KEY = os.getenv("DEPLOYER_PRIVATE_KEY", "")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS", "")

supabase: Client = create_client(SUPABASE_URL, SERVICE_KEY)

def anchor_dossier_on_chain(dossier_id: str, user_id: str) -> Tuple[str, str]:
    """
    Anchor dossier hash on Sepolia blockchain
    
    Args:
        dossier_id: Dossier UUID
        user_id: User UUID
        
    Returns:
        Tuple of (tx_hash, explorer_url)
    """
    # Get dossier hash
    dossier = supabase.table("dossiers").select("sha256").eq("id", dossier_id).execute()
    
    if not dossier.data:
        raise Exception("Dossier not found")
    
    dossier_hash = dossier.data[0]["sha256"]
    
    # Check if blockchain integration is configured
    if not CONTRACT_ADDRESS or CONTRACT_ADDRESS == "":
        # Return mock/placeholder for development
        print(f"[Blockchain] Warning: CONTRACT_ADDRESS not configured, using mock anchoring")
        tx_hash = f"0xMOCK_{dossier_hash[:16]}"
        explorer_url = f"https://sepolia.etherscan.io/tx/{tx_hash}"
        
        # Store certificate
        supabase.table("blockchain_certificates").insert({
            "dossier_id": dossier_id,
            "user_id": user_id,
            "dossier_hash": dossier_hash,
            "tx_hash": tx_hash,
            "explorer_url": explorer_url
        }).execute()
        
        return tx_hash, explorer_url
    
    # Real blockchain anchoring
    try:
        # Call Node.js script that uses ethers.js to anchor
        script_path = os.path.join(os.path.dirname(__file__), "..", "blockchain", "anchor.js")
        
        if not os.path.exists(script_path):
            raise Exception("Blockchain anchor script not found. Please set up blockchain integration.")
        
        result = subprocess.run(
            ["node", script_path, dossier_hash, CONTRACT_ADDRESS, DEPLOYER_PRIVATE_KEY, HARDHAT_RPC_URL],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            raise Exception(f"Blockchain anchoring failed: {result.stderr}")
        
        # Parse result
        output = json.loads(result.stdout)
        tx_hash = output["tx_hash"]
        explorer_url = f"https://sepolia.etherscan.io/tx/{tx_hash}"
        
        print(f"[Blockchain] ✓ Anchored on Sepolia: {tx_hash}")
        
        # Store certificate
        supabase.table("blockchain_certificates").insert({
            "dossier_id": dossier_id,
            "user_id": user_id,
            "dossier_hash": dossier_hash,
            "tx_hash": tx_hash,
            "explorer_url": explorer_url
        }).execute()
        
        return tx_hash, explorer_url
        
    except subprocess.TimeoutExpired:
        raise Exception("Blockchain transaction timeout after 60 seconds")
    except json.JSONDecodeError as e:
        raise Exception(f"Failed to parse blockchain response: {str(e)}")
    except Exception as e:
        raise Exception(f"Blockchain anchoring error: {str(e)}")

def verify_anchor(tx_hash: str) -> dict:
    """
    Verify a blockchain anchor
    
    Args:
        tx_hash: Transaction hash
        
    Returns:
        Certificate data
    """
    result = supabase.table("blockchain_certificates").select("*").eq("tx_hash", tx_hash).execute()
    
    if not result.data:
        raise Exception("Certificate not found")
    
    return result.data[0]

def get_dossier_certificate(dossier_id: str) -> dict:
    """
    Get blockchain certificate for a dossier
    
    Args:
        dossier_id: Dossier UUID
        
    Returns:
        Certificate data
    """
    result = supabase.table("blockchain_certificates").select("*").eq("dossier_id", dossier_id).execute()
    
    if not result.data:
        return None
    
    return result.data[0]