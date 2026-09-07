import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db
from app.schemas.schemas import HealthResponse

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    """Service health check endpoint."""
    status = "OK"
    db_status = "OK"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "ERROR"
        status = "DEGRADED"

    return {
        "status": status,
        "database": db_status,
        "ocr_engine": "OK", 
        "blockchain_node": "SIMULATED", 
        "timestamp": datetime.datetime.now().isoformat()
    }
