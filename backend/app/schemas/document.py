"""
Document Pydantic schemas
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class DocumentBase(BaseModel):
    """Base document schema"""
    file_name: str
    fund_id: Optional[int] = None
    # Tambahkan field metadata Phase 2
    title: Optional[str] = None
    date: Optional[str] = None
    document_number: Optional[str] = None
    document_type: Optional[str] = None


class DocumentCreate(DocumentBase):
    """Document creation schema"""
    file_path: str


class DocumentUpdate(BaseModel):
    """Document update schema"""
    parsing_status: Optional[str] = None
    error_message: Optional[str] = None
    # Opsional: tambahkan metadata di sini jika perlu update manual
    title: Optional[str] = None
    date: Optional[str] = None
    document_number: Optional[str] = None
    document_type: Optional[str] = None


class Document(DocumentBase):
    """Document response schema"""
    id: int
    file_path: Optional[str] = None
    upload_date: datetime
    parsing_status: str
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True


class DocumentStatus(BaseModel):
    """Document parsing status"""
    document_id: int
    status: str
    progress: Optional[float] = None
    error_message: Optional[str] = None


class DocumentUploadResponse(BaseModel):
    """Document upload response"""
    document_id: int
    task_id: Optional[str] = None
    status: str
    message: str