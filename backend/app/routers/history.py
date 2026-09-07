import json
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import models
from app.schemas.schemas import HistoryResponse, HistoryItem
from app.core.exceptions import DocumentNotFoundError

router = APIRouter()

@router.get("/history", response_model=HistoryResponse)
def get_analysis_history(limit: int = 20, db: Session = Depends(get_db)):
    """Return saved inspections for the dashboard."""
    total_scanned = db.query(models.VerificationReport).count()
    tampered_flags = db.query(models.VerificationReport).filter(
        models.VerificationReport.tamper_score > 30
    ).count()
    average_risk = db.query(func.avg(models.VerificationReport.risk_score)).scalar()

    documents = db.query(models.Document).order_by(
        models.Document.id.desc()
    ).limit(min(max(limit, 1), 100)).all()
    
    history = []
    for document in documents:
        report = db.query(models.VerificationReport).filter(
            models.VerificationReport.document_id == document.id
        ).order_by(models.VerificationReport.id.desc()).first()
        
        audit = db.query(models.AuditLog).filter(
            models.AuditLog.report_id == report.id
        ).first() if report else None

        history.append({
            "document_id": document.id,
            "document_type": document.document_type,
            "extracted_fields": json.loads(document.extracted_fields or "{}"),
            "ocr": {"status": report.ocr_status if report else "unknown"},
            "validation": {"status": report.validation_status if report else "unknown"},
            "tampering": {"tamper_score": report.tamper_score if report else 0},
            "face_match": {"similarity": report.face_score} if report and report.face_score is not None else {},
            "risk_score": report.risk_score if report else 0,
            "risk_level": report.risk_level if report else "UNKNOWN",
            "created_at": report.created_at.isoformat() if report and report.created_at else "",
            "audit": {
                "report_id": f"DB-{report.id}" if report else None,
                "report_hash": audit.blockchain_hash if audit else None,
                "transaction_id": audit.transaction_id if audit else None,
                "blockchain_status": "VERIFIED" if audit else "NOT_AVAILABLE"
            }
        })

    return {
        "items": history,
        "summary": {
            "total_scanned": total_scanned,
            "tampered_flags": tampered_flags,
            "average_risk": round(float(average_risk or 0), 1)
        }
    }


@router.delete("/history/{document_id}")
def delete_history_item(document_id: int, db: Session = Depends(get_db)):
    """Delete a document history record."""
    document = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not document:
        raise DocumentNotFoundError(f"Document {document_id} not found")
        
    db.delete(document)  # Cascades due to relationships (if configured) or manual cleanup needed
    db.commit()
    return {"status": "success", "message": f"Document {document_id} deleted"}
