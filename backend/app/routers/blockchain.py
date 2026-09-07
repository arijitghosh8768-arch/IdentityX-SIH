from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.blockchain import verify_on_blockchain

router = APIRouter()

class VerifyRequest(BaseModel):
    report_id: str
    expected_hash: str

@router.post("/verify-hash")
def verify_hash(req: VerifyRequest):
    """Verify a report hash against the blockchain."""
    is_valid = verify_on_blockchain(req.report_id, req.expected_hash)
    if not is_valid:
        raise HTTPException(status_code=400, detail="Hash verification failed")
    
    return {"status": "success", "message": "Hash verified on blockchain"}
