from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------
# Nested structures for Analysis Results
# ---------------------------------------------------------

class OCRResult(BaseModel):
    status: str
    extracted_fields: Dict[str, Any]
    mrz_lines: Optional[List[str]] = None
    raw_text_segments: Optional[List[str]] = None


class ValidationCheck(BaseModel):
    required_fields_present: bool
    expiry_valid: bool
    mrz_consistent: bool


class ValidationResult(BaseModel):
    status: str
    checks: ValidationCheck
    warnings: List[str]
    mrz_mismatches: List[str]


class TamperResult(BaseModel):
    status: str
    is_tampered: bool
    tamper_score: float
    suspicious_regions_count: int
    heatmap_image: Optional[str] = None
    message: Optional[str] = None


class FaceMatchResult(BaseModel):
    status: str
    match: Optional[bool] = None
    similarity: Optional[float] = None
    distance: Optional[float] = None
    message: Optional[str] = None


class AuditTrailInfo(BaseModel):
    report_id: str
    document_hash: str
    report_hash: str
    blockchain_status: str
    transaction_id: str
    timestamp: str


# ---------------------------------------------------------
# API Response Models
# ---------------------------------------------------------

class AnalyzeResponse(BaseModel):
    ocr: OCRResult
    mrz: Dict[str, Any]
    validation: ValidationResult
    tampering: TamperResult
    face_match: FaceMatchResult
    risk_score: int
    risk_level: str
    audit: AuditTrailInfo


class HistoryItem(BaseModel):
    document_id: int
    document_type: str
    extracted_fields: Dict[str, Any]
    ocr: Dict[str, Any]
    validation: Dict[str, Any]
    tampering: Dict[str, Any]
    face_match: Dict[str, Any]
    risk_score: int
    risk_level: str
    audit: Dict[str, Any]
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class HistorySummary(BaseModel):
    total_scanned: int
    tampered_flags: int
    average_risk: float


class HistoryResponse(BaseModel):
    items: List[HistoryItem]
    summary: HistorySummary


class HealthResponse(BaseModel):
    status: str
    database: str
    ocr_engine: str
    blockchain_node: str
    timestamp: str


class StatsResponse(BaseModel):
    total_documents: int
    average_risk_score: float
    tampered_documents: int
    documents_by_type: Dict[str, int]
    risk_levels: Dict[str, int]
