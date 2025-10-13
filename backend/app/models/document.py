# app/models/document.py
"""
Document database model
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class Document(Base):
    """Document model"""
    
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    fund_id = Column(Integer, ForeignKey("funds.id"))
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500))
    upload_date = Column(DateTime, default=datetime.utcnow)
    parsing_status = Column(String(50), default="pending") 
    error_message = Column(Text)
    
    title = Column(String(500), nullable=True)
    date = Column(String(100), nullable=True) 
    document_number = Column(String(200), nullable=True)
    document_type = Column(String(200), nullable=True)
    
    # Relationships
    fund = relationship("Fund", back_populates="documents")
    capital_calls = relationship("CapitalCall", back_populates="document")
    distributions = relationship("Distribution", back_populates="document")
    adjustments = relationship("Adjustment", back_populates="document")