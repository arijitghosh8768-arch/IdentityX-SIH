import json
import fitz  # PyMuPDF
from fastapi import APIRouter, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import models
from app.schemas.schemas import AnalyzeResponse
from app.services.ocr import process_document_ocr
from app.services.validation import validate_document
from app.services.face import verify_face
from app.services.tamper import detect_tampering
from app.services.risk import calculate_risk_score
from app.services.blockchain import log_to_blockchain
from app.core.logging_config import get_logger
from app.core.exceptions import DocumentProcessingError

logger = get_logger("router.analyze")
router = APIRouter()

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_document(
    document: UploadFile = File(...),
    live_face: UploadFile = File(None),
    document_type: str = Form("passport"),
    db: Session = Depends(get_db)
):
    """
    Main endpoint for the prototype. Receives a document and returns the combined analysis.
    """
    logger.info(f"Starting analysis for {document.filename} (type: {document_type})")
    
    # Read the file bytes
    contents = await document.read()
    
    # Handle PDF uploads
    if document.filename.lower().endswith('.pdf') or document.content_type == 'application/pdf':
        try:
            pdf_document = fitz.open(stream=contents, filetype="pdf")
            if len(pdf_document) == 0:
                raise DocumentProcessingError("Empty PDF provided.")
            # Extract first page as an image (PNG)
            page = pdf_document[0]
            pix = page.get_pixmap(dpi=300)
            contents = pix.tobytes("png")
            pdf_document.close()
        except DocumentProcessingError:
            raise
        except Exception as e:
            logger.error(f"PDF Parsing Error: {e}")
            raise DocumentProcessingError(f"Failed to parse PDF: {str(e)}")
            
    # 1. OCR
    logger.info("Running OCR...")
    ocr_results = process_document_ocr(contents, document_type)
    
    # 2. Validation
    logger.info("Running Validation...")
    mrz_data = ocr_results.get("mrz", {})
    mrz_consistency = ocr_results.get("verification", {})
    
    validation_results = validate_document(
        ocr_results.get("extracted_fields", {}),
        mrz_consistency,
        document_type
    )
    
    # 3. Face Verification
    logger.info("Running Face Verification...")
    face_match_results = {"status": "pending", "message": "No live face provided"}
    if live_face:
        live_face_contents = await live_face.read()
        face_match_results = verify_face(contents, live_face_contents)
    
    # 4. Tampering Detection
    logger.info("Running Tamper Detection...")
    tampering_results = detect_tampering(contents)
    
    # 5. Risk Score Engine
    logger.info("Calculating Risk Score...")
    risk_data = calculate_risk_score(
        validation_status=validation_results.get("status", "UNKNOWN"),
        face_match=face_match_results,
        tamper_score=tampering_results.get("tamper_score", 0),
        mrz_consistent=validation_results.get("checks", {}).get("mrz_consistent", True),
        missing_fields=validation_results.get("warnings", []),
        has_live_face=bool(live_face)
    )
    
    # Pack result data
    result_data = {
        "ocr": ocr_results,
        "mrz": mrz_data,
        "validation": validation_results,
        "tampering": tampering_results,
        "face_match": face_match_results,
        "risk_score": risk_data["score"],
        "risk_level": risk_data["level"]
    }
    
    # 6. Blockchain Audit
    logger.info("Logging to Blockchain...")
    audit_trail = log_to_blockchain(result_data, contents)
    result_data["audit"] = audit_trail

    # Store in DB
    logger.info("Saving to Database...")
    try:
        document_hash = audit_trail["document_hash"]
        stored_document = db.query(models.Document).filter(
            models.Document.document_hash == document_hash
        ).first()

        if stored_document is None:
            stored_document = models.Document(
                document_type=document_type,
                document_hash=document_hash,
                extracted_fields=json.dumps(ocr_results.get("extracted_fields", {}), sort_keys=True)
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
            risk_score=risk_data["score"],
            risk_level=risk_data["level"],
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
    except Exception as e:
        logger.error(f"Database save error: {e}")
        db.rollback()
        raise
    
    logger.info(f"Analysis complete for {document.filename}. Score: {risk_data['score']} ({risk_data['level']})")
    return result_data
