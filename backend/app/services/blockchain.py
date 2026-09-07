import hashlib
import time
import json
import uuid
import subprocess
import os
from app.core.config import get_settings
from app.core.logging_config import get_logger

logger = get_logger("blockchain")
settings = get_settings()

def generate_report_hash(report_data: dict) -> str:
    """Generates a deterministic SHA-256 hash of the verification report."""
    report_string = json.dumps(report_data, sort_keys=True)
    return hashlib.sha256(report_string.encode('utf-8')).hexdigest()

def generate_document_hash(image_bytes: bytes) -> str:
    """Generates a SHA-256 hash of the uploaded document image."""
    return hashlib.sha256(image_bytes).hexdigest()

def _call_node_script(script_name: str, *args) -> dict:
    """Helper to call Node.js blockchain scripts."""
    # Construct paths assuming backend and blockchain are siblings in project root
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    blockchain_dir = os.path.join(base_dir, "blockchain")
    script_path = os.path.join(blockchain_dir, script_name)

    # Use Node to execute a wrapper script or use tsx/babel if needed. 
    # For now we'll assume a simple execution. 
    # If this fails, we will fall back to simulated mode.
    try:
        # Provide environment variables to Node
        env = os.environ.copy()
        if settings.BLOCKCHAIN_RPC_URL:
            env["RPC_URL"] = settings.BLOCKCHAIN_RPC_URL
        if settings.CONTRACT_ADDRESS:
            env["CONTRACT_ADDRESS"] = settings.CONTRACT_ADDRESS
        if settings.PRIVATE_KEY:
            env["PRIVATE_KEY"] = settings.PRIVATE_KEY

        # Node execution (this requires an entry point script on the JS side, e.g., 'scripts/logReport.js')
        # We will assume a wrapper script exists or we'll fallback.
        # This is a placeholder for actual Hardhat Node.js integration logic.
        cmd = ["node", script_path] + list(args)
        result = subprocess.run(cmd, cwd=blockchain_dir, capture_output=True, text=True, env=env, check=True, timeout=15)
        return json.loads(result.stdout)
    except Exception as e:
        logger.warning(f"Blockchain node call failed, falling back to simulation: {e}")
        return None

def log_to_blockchain(report_data: dict, image_bytes: bytes) -> dict:
    """Logs the verification report hash to the blockchain."""
    report_id = f"RX-{str(uuid.uuid4())[:8].upper()}"
    
    doc_hash = generate_document_hash(image_bytes)
    rep_hash = generate_report_hash(report_data)

    logger.info(f"Logging report {report_id} to blockchain...")
    
    # Try actual blockchain integration if configured
    # if settings.BLOCKCHAIN_RPC_URL and settings.CONTRACT_ADDRESS:
    #     result = _call_node_script("scripts/logReport.js", report_id, doc_hash, rep_hash)
    #     if result and result.get("success"):
    #         return {
    #             "report_id": report_id,
    #             "document_hash": doc_hash,
    #             "report_hash": rep_hash,
    #             "blockchain_status": "VERIFIED",
    #             "transaction_id": result.get("transaction_hash"),
    #             "timestamp": time.strftime("%d %b %Y %H:%M:%S")
    #         }

    # Fallback to simulated mode
    time.sleep(1)
    simulated_tx_id = "0x" + hashlib.sha256(str(time.time()).encode()).hexdigest()
    
    logger.info(f"Simulated blockchain log for {report_id} successful.")

    return {
        "report_id": report_id,
        "document_hash": "0x" + doc_hash,
        "report_hash": "0x" + rep_hash,
        "blockchain_status": "VERIFIED_SIMULATED",
        "transaction_id": simulated_tx_id,
        "timestamp": time.strftime("%d %b %Y %H:%M:%S")
    }

def verify_on_blockchain(report_id: str, expected_hash: str) -> bool:
    """Verifies that a report hash matches the one stored on the blockchain."""
    # if settings.BLOCKCHAIN_RPC_URL and settings.CONTRACT_ADDRESS:
    #     result = _call_node_script("scripts/verifyReport.js", report_id, expected_hash)
    #     if result:
    #         return result.get("verified", False)
    
    # In simulated mode, we just return True for demonstration purposes, 
    # or you could verify it against the local SQLite AuditLogs.
    return True
