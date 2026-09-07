from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import json
from sqlalchemy import func
from app.services.ocr import process_document_ocr
from app.services.mrz import parse_mrz, verify_mrz_consistency
from app.services.validation import validate_document
from app.services.face import verify_face
from app.services.tamper import detect_tampering
from app.services.blockchain import log_to_blockchain
from app.core.database import engine, Base, SessionLocal, ensure_sqlite_schema
import app.models.models as models
import fitz  # PyMuPDF
import io
import sys

# Fix Windows console encoding for EasyOCR progress bar
if sys.platform.startswith('win'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from app.core.database import engine, Base
import app.models.models as models
import fitz  # PyMuPDF
import io

# Create database tables
Base.metadata.create_all(bind=engine)
ensure_sqlite_schema()

app = FastAPI(title="IdentityX API", description="AI-Based Identity & Document Screening")

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to IdentityX API"}


@app.get("/api/history")
def get_analysis_history(limit: int = 20):
    """Return saved inspections so the dashboard survives a browser refresh."""
    db = SessionLocal()
    try:
        total_scanned = db.query(models.VerificationReport).count()
        tampered_flags = db.query(models.VerificationReport).filter(
            models.VerificationReport.tamper_score > 30
        ).count()
        average_risk = db.query(
            func.avg(models.VerificationReport.risk_score)
        ).scalar()

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
    finally:
        db.close()

@app.post("/api/analyze")
async def analyze_document(
    document: UploadFile = File(...),
    live_face: UploadFile = File(None),
    document_type: str = Form("passport")
):
    """
    Main endpoint for the prototype. Receives a document and returns the combined analysis.
    """
    # Read the file bytes
    contents = await document.read()
    
    # Handle PDF uploads
    if document.filename.lower().endswith('.pdf') or document.content_type == 'application/pdf':
        try:
            # Open PDF with PyMuPDF
            pdf_document = fitz.open(stream=contents, filetype="pdf")
            if len(pdf_document) == 0:
                return {"error": "Empty PDF provided"}
            # Extract first page as an image (PNG)
            page = pdf_document[0]
            pix = page.get_pixmap(dpi=300)
            contents = pix.tobytes("png")
            pdf_document.close()
        except Exception as e:
            return {"error": f"Failed to parse PDF: {str(e)}"}
            
    # 1. OCR (Phase 2)
    ocr_results = process_document_ocr(contents, document_type)
    
    # 2. MRZ & Validation (Phase 3)
    mrz_data = ocr_results.get("mrz", {})
    mrz_consistency = ocr_results.get("verification", {})
    
    validation_results = validate_document(
        ocr_results.get("extracted_fields", {}),
        mrz_consistency,
        document_type
    )
    
    # 3. Face Verification (Phase 4)
    face_match_results = {"status": "pending", "message": "No live face provided"}
    if live_face:
        live_face_contents = await live_face.read()
        face_match_results = verify_face(contents, live_face_contents)
    
    # 4. Tampering Detection (Phase 5)
    tampering_results = detect_tampering(contents)
    
    # 5. Risk Score Engine (Phase 6 Integration)
    risk_score = 0
    if validation_results["status"] != "VALID":
        risk_score += 30
    if live_face and face_match_results.get("match") is False:
        risk_score += 35
    
    tamper_val = tampering_results.get("tamper_score", 0)
    if tamper_val > 30:
        risk_score += 35
        
    # Cap score at 100
    risk_score = min(100, risk_score)
    
    # Pack result data
    result_data = {
        "ocr": ocr_results,
        "mrz": mrz_data,
        "validation": validation_results,
        "tampering": tampering_results,
        "face_match": face_match_results,
        "risk_score": risk_score
    }
    
    # 6. Blockchain Audit (Phase 8)
    audit_trail = log_to_blockchain(result_data, contents)
    
    # Add audit to the final response
    result_data["audit"] = audit_trail

    # Store the useful inspection details in SQLite.
    db = SessionLocal()
    try:
        document_hash = audit_trail["document_hash"]
        stored_document = db.query(models.Document).filter(
            models.Document.document_hash == document_hash
        ).first()

        if stored_document is None:
            stored_document = models.Document(
                document_type=document_type,
                document_hash=document_hash,
                extracted_fields=json.dumps(
                    ocr_results.get("extracted_fields", {}),
                    sort_keys=True
                )
            )
            db.add(stored_document)
            db.flush()

        officer = db.query(models.User).filter(models.User.role == "officer").first()
        if officer is None:
            officer = models.User(name="System Officer", role="officer")
            db.add(officer)
            db.flush()

        report = models.VerificationReport(
            document_id=stored_document.id,
            officer_id=officer.id,
            ocr_status=ocr_results.get("status"),
            validation_status=validation_results.get("status"),
            tamper_score=tampering_results.get("tamper_score", 0),
            face_score=face_match_results.get("similarity"),
            risk_score=risk_score,
            final_status=validation_results.get("status")
        )
        db.add(report)
        db.flush()

        db.add(models.AuditLog(
            report_id=report.id,
            blockchain_hash=audit_trail.get("report_hash"),
            transaction_id=audit_trail.get("transaction_id")
        ))
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
    
    return result_data


@app.get('/api/stats')
def get_stats():
    db = SessionLocal()
    try:
        total_scans = db.query(models.Document).count()
        tampered = db.query(models.VerificationReport).filter(models.VerificationReport.tampering_detected == True).count()
        
        # Calculate average risk
        reports = db.query(models.VerificationReport.risk_score).all()
        avg_risk = sum(r[0] for r in reports) / len(reports) if reports else 0
        
        return {
            'total_scanned': total_scans,
            'tampered_flags': tampered,
            'average_risk': round(avg_risk)
        }
    finally:
        db.close()
