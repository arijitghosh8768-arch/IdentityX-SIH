from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    role = Column(String, default="officer")
    
    reports = relationship("VerificationReport", back_populates="officer")

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    document_type = Column(String, default="passport")
    document_hash = Column(String, unique=True, index=True) # SHA-256 of the image
    extracted_fields = Column(Text)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    reports = relationship("VerificationReport", back_populates="document")

class VerificationReport(Base):
    __tablename__ = "verification_reports"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    officer_id = Column(Integer, ForeignKey("users.id"))
    
    # Module Statuses
    ocr_status = Column(String)
    validation_status = Column(String)
    tamper_score = Column(Float)
    face_score = Column(Float)
    
    # Final Results
    risk_score = Column(Integer)
    final_status = Column(String)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    document = relationship("Document", back_populates="reports")
    officer = relationship("User", back_populates="reports")
    audit_log = relationship("AuditLog", back_populates="report", uselist=False)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("verification_reports.id"), unique=True)
    
    # Blockchain Audit Info
    blockchain_hash = Column(String) # The hash written to the blockchain
    transaction_id = Column(String)  # The blockchain transaction ID (e.g. Ethereum Tx)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    report = relationship("VerificationReport", back_populates="audit_log")
