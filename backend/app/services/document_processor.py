"""
Document processing service for Phase 1: Metadata Extraction
"""
from typing import Dict, Any
import pdfplumber
from datetime import datetime
import re
import os

class DocumentProcessor:
    """Process PDF documents and extract basic metadata for Phase 1"""
    
    def __init__(self):
        pass
    
    async def process_document(self, file_path: str, document_id: int, fund_id: int) -> Dict[str, Any]:
        """
        Extract basic metadata from PDF for Phase 1
        
        Returns:
            dict with 'status' and optional 'error'
        """
        try:
            # Ekstrak metadata dasar
            metadata = self._extract_metadata(file_path)
            
            # Simpan metadata ke database (opsional di sini, atau di task lain)
            # Untuk Phase 1, cukup pastikan tidak error
            
            return {"status": "completed"}
            
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }

    def _extract_metadata(self, file_path: str) -> dict:
        """Ekstrak metadata sederhana dari PDF"""
        filename = os.path.basename(file_path)
        
        metadata = {
            "title": self._generate_title(filename),
            "date": str(datetime.now().date()),
            "document_number": self._generate_doc_number(filename),
            "document_type": "Dokumen Umum"
        }

        try:
            with pdfplumber.open(file_path) as pdf:
                if len(pdf.pages) > 0:
                    first_page = pdf.pages[0]
                    text = first_page.extract_text() or ""
                    
                    if text.strip():
                        lines = [line.strip() for line in text.split("\n") if line.strip()]
                        if lines:
                            # Ambil baris pertama sebagai judul (heuristic sederhana)
                            metadata["title"] = lines[0][:100]
                    
                    # Cari tanggal dalam teks (format sederhana)
                    date_match = re.search(r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}", text)
                    if date_match:
                        metadata["date"] = date_match.group(0)
                        
        except Exception as e:
            # Jangan gagal hanya karena ekstraksi teks error
            print(f"Warning: PDF text extraction failed: {e}")
        
        return metadata

    def _generate_title(self, filename: str) -> str:
        name = os.path.splitext(filename)[0]
        return name.replace("_", " ").replace("-", " ").title() or "Dokumen Tanpa Judul"

    def _generate_doc_number(self, filename: str) -> str:
        clean_name = re.sub(r"[^a-zA-Z0-9]", "", os.path.splitext(filename)[0])
        return f"DOC-{clean_name[:10].upper()}" if clean_name else "DOC-DEFAULT"