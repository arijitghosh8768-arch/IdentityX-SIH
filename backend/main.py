from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from app.services.ocr import process_document_ocr
from app.services.mrz import parse_mrz, verify_mrz_consistency
from app.services.validation import validate_document
from app.services.face import verify_face
from app.services.tamper import detect_tampering
from app.services.blockchain import log_to_blockchain
from app.core.database import engine, Base
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

@app.post("/api/analyze")
async def analyze_document(
    document: UploadFile = File(...),
    live_face: UploadFile = File(None)
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
    ocr_results = process_document_ocr(contents)
    
    # 2. MRZ & Validation (Phase 3)
    mrz_data = parse_mrz(ocr_results.get("mrz_lines", []))
    mrz_consistency = verify_mrz_consistency(ocr_results.get("extracted_fields", {}), mrz_data)
    
    validation_results = validate_document(
        ocr_results.get("extracted_fields", {}), 
        mrz_consistency
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
    
    return result_data
