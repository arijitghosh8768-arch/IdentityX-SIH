import hashlib
import time
import json
import uuid

def generate_report_hash(report_data: dict) -> str:
    """
    Generates a deterministic SHA-256 hash of the verification report.
    """
    # Sort keys to ensure consistent hashing
    report_string = json.dumps(report_data, sort_keys=True)
    return hashlib.sha256(report_string.encode('utf-8')).hexdigest()

def generate_document_hash(image_bytes: bytes) -> str:
    """
    Generates a SHA-256 hash of the uploaded document image.
    """
    return hashlib.sha256(image_bytes).hexdigest()

def log_to_blockchain(report_data: dict, image_bytes: bytes) -> dict:
    """
    Simulates logging the hash to an Ethereum Sepolia Smart Contract.
    In a real scenario, this would use web3.py to call the AuditTrail contract.
    """
    report_id = f"RX-{str(uuid.uuid4())[:8].upper()}"
    
    doc_hash = generate_document_hash(image_bytes)
    rep_hash = generate_report_hash(report_data)
    
    # ---------------------------------------------------------
    # TODO for actual Hackathon deployment:
    # 1. from web3 import Web3
    # 2. w3 = Web3(Web3.HTTPProvider("YOUR_SEPOLIA_RPC_URL"))
    # 3. contract = w3.eth.contract(address=..., abi=...)
    # 4. tx = contract.functions.logReport(report_id, doc_hash, rep_hash).build_transaction(...)
    # 5. signed_tx = w3.eth.account.sign_transaction(tx, private_key=...)
    # 6. tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    # ---------------------------------------------------------
    
    # Simulating a 1-second blockchain transaction delay
    time.sleep(1)
    
    # Simulated Ethereum Transaction Hash
    simulated_tx_id = "0x" + hashlib.sha256(str(time.time()).encode()).hexdigest()
    
    return {
        "report_id": report_id,
        "document_hash": doc_hash,
        "report_hash": rep_hash,
        "blockchain_status": "VERIFIED",
        "transaction_id": simulated_tx_id,
        "timestamp": time.strftime("%d %b %Y %H:%M:%S")
    }
