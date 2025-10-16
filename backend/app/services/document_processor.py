# backend/app/services/document_processor.py
"""
Enhanced Document Processing Service (Docling 2.55.1)
For InterOpera Phase 2 — handles Capital Calls, Distributions, Adjustments.
"""
from typing import Dict, Any, List
from datetime import datetime
import re
import traceback
import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
# --- Docling imports ---
from docling.document_converter import DocumentConverter
from docling_core.types import DoclingDocument
from docling_core.types.doc import TableItem
# --- Local imports ---
from app.models.fund import Fund
from app.models.document import Document as DBDocument
from app.models.transaction import CapitalCall, Distribution, Adjustment
from app.db.session import SessionLocal
from app.core.config import settings
from app.services.vector_store import VectorStore
from sqlalchemy.orm import Session


class DocumentProcessor:
    """Process PDF using Docling and save structured data to PostgreSQL + Vector DB"""

    def __init__(self):
        self.converter = DocumentConverter()
        self.vector_store = VectorStore()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            length_function=len,
        )
        print("✅ Docling: DocumentConverter and VectorStore initialized.")

    async def process_document(self, file_path: str, document_id: int, fund_id: int) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            print(f"\n📄 Docling: Processing file {file_path}")
            
            # --- ✅ PERBAIKAN UTAMA: JANGAN PERNAH MENEBAK FUND_ID ---
            if not fund_id:
                raise ValueError("❌ Fund ID is required. Please specify fund_id during upload.")
            print(f"🔗 Using provided fund_id: {fund_id}")
            # --- AKHIR PERBAIKAN UTAMA ---

            # --- 1. Convert Document ---
            conversion_result = self.converter.convert(file_path)
            print("⚙️ Docling: Conversion completed.")
            if not hasattr(conversion_result, "document"):
                raise ValueError("Docling conversion did not produce a document object.")
            doc: DoclingDocument = conversion_result.document
            print(f"📘 Got DoclingDocument object ({type(doc)})")
            self._inspect_doc_structure(doc)

            # --- 2. Extract text & metadata ---
            text = self._extract_text_from_doc(doc)
            print(f"📝 Extracted text length: {len(text)} chars")
            metadata = self._extract_metadata(text, file_path)
            print(f"📑 Metadata extracted: {metadata}")

            # --- 3. Extract tables ---
            tables = self._extract_tables_from_doc(doc)
            print(f"📊 Extracted {len(tables)} table(s)")

            # --- 4. Ensure fund_id is set in DB ---
            doc_db = db.query(DBDocument).filter(DBDocument.id == document_id).first()
            if not doc_db:
                raise ValueError(f"Document ID {document_id} not found")
            if not doc_db.fund_id:
                doc_db.fund_id = fund_id
                db.commit()
                print(f"🔗 Assigned fund_id {fund_id} to document {document_id}")

            # --- 5. Save structured data to SQL ---
            self._save_to_db(db, document_id, metadata, tables)

            # --- 6. Save unstructured text to Vector DB ---
            await self._save_text_to_vector_store(text, document_id, fund_id)

            return {"status": "completed"}

        except Exception as e:
            print(f"❌ Processing error: {e}")
            traceback.print_exc()
            return {"status": "failed", "error": str(e)}
        finally:
            db.close()

    # ----------------------------------------------------------------------
    # 🔍 INSPECTION
    # ----------------------------------------------------------------------
    def _inspect_doc_structure(self, doc: DoclingDocument):
        try:
            print("\n🔍 Docling Inspection: Document attributes:")
            attrs = [a for a in dir(doc) if not a.startswith("_")]
            print("  →", attrs)
            if hasattr(doc, "tables") and doc.tables:
                print(f"🔍 Found {len(doc.tables)} table(s). Inspecting first one:")
                t = doc.tables[0]
                t_attrs = [a for a in dir(t) if not a.startswith("_")]
                print("  → Table attributes:", t_attrs)
        except Exception as e:
            print(f"⚠️ Docling: Inspection failed: {e}")

    # ----------------------------------------------------------------------
    # 🧾 TEXT EXTRACTION
    # ----------------------------------------------------------------------
    def _extract_text_from_doc(self, doc: DoclingDocument) -> str:
        try:
            if hasattr(doc, "export_to_text"):
                return doc.export_to_text()
            elif hasattr(doc, "pages"):
                return "\n".join(
                    " ".join(cell.text for cell in getattr(page, "cells", []) if getattr(cell, "text", None))
                    for page in doc.pages
                )
        except Exception as e:
            print(f"⚠️ Text extraction failed: {e}")
        return ""

    # ----------------------------------------------------------------------
    # 📦 SAVE TEXT TO VECTOR STORE
    # ----------------------------------------------------------------------
    async def _save_text_to_vector_store(self, text: str, document_id: int, fund_id: int):
        if not text.strip():
            print("⚠️ No text to embed.")
            return
        chunks = self.text_splitter.split_text(text)
        print(f"✂️ Split text into {len(chunks)} chunks")
        metadata = {
            "document_id": document_id,
            "fund_id": fund_id,
            "source_type": "pdf_text"
        }
        for i, chunk in enumerate(chunks):
            meta = {**metadata, "chunk_index": i}
            await self.vector_store.add_document(content=chunk, metadata=meta)
        print(f"✅ Embedded {len(chunks)} text chunks into vector store.")

    # ----------------------------------------------------------------------
    # 🧩 TABLE EXTRACTION
    # ----------------------------------------------------------------------
    def _extract_tables_from_doc(self, doc: DoclingDocument) -> List[dict]:
        tables = []
        if not hasattr(doc, "tables") or not doc.tables:
            print("⚠️ No tables detected in document.")
            return tables
        for i, table_item in enumerate(doc.tables):
            try:
                if not isinstance(table_item, TableItem):
                    continue
                df = table_item.export_to_dataframe()
                if df.empty:
                    continue
                # === Normalisasi kolom: bersihkan spasi, simbol, dan lowercase ===
                normalized_columns = []
                for col in df.columns:
                    clean_col = str(col).strip().replace(" (USD)", "").replace("$", "").replace("*", "")
                    normalized_columns.append(clean_col)
                df.columns = normalized_columns
                # ============================================================
                headers = [str(c) for c in df.columns]
                header_text = " ".join(headers).lower()
                table_type = "Unknown"
                # === Deteksi berdasarkan konten kolom "Type" terlebih dahulu ===
                if "type" in [c.lower() for c in df.columns]:
                    type_values = " ".join(str(v).lower() for v in df["Type"].dropna().unique())
                    if "recallable dist" in type_values:
                        table_type = "adjustments"  # <-- Perbaikan: Tabel ini adalah Adjustments
                    elif "return" in type_values or "income" in type_values:
                        table_type = "distributions"
                    elif "capital call adj" in type_values or "contribution adjustment" in type_values:
                        table_type = "adjustments"
                    elif "call" in type_values:
                        table_type = "capital_calls"
                # === Jika masih unknown, cek header ===
                if table_type == "Unknown":
                    if any(k in header_text for k in ["distrib", "payout", "return", "income"]):
                        table_type = "distributions"
                    elif any(k in header_text for k in ["adjust", "correction", "fee", "reclass"]):
                        table_type = "adjustments"
                    elif any(k in header_text for k in ["capital", "call", "called"]):
                        table_type = "capital_calls"
                # === Fallback berdasarkan posisi ===
                if table_type == "Unknown":
                    fallback_types = ["capital_calls", "distributions", "adjustments"]
                    if i < len(fallback_types):
                        table_type = fallback_types[i]
                        print(f"🔍 Fallback: Assigning table {i} as '{table_type}'")

                print(f"📄 Table {i}: detected type '{table_type}' with headers = {headers}")
                tables.append({"type": table_type, "data": df.to_dict(orient="records")})
            except Exception as e:
                print(f"⚠️ Error processing table {i}: {e}")
                traceback.print_exc()
        print(f"✅ Total tables extracted: {len(tables)}")
        return tables

    # ----------------------------------------------------------------------
    # 🧠 METADATA EXTRACTION
    # ----------------------------------------------------------------------
    def _extract_metadata(self, text: str, file_path: str) -> dict:
        metadata = {
            "title": "Untitled Document",
            "date": str(datetime.now().date()),
            "document_number": "DOC-DEFAULT",
            "document_type": "General Document",
        }
        if text.strip():
            first_line = next((l for l in text.splitlines() if l.strip()), "")
            if len(first_line) > 5:
                metadata["title"] = first_line[:200]
        if "capital call" in text.lower():
            metadata["document_type"] = "Capital Call"
        elif "distribution" in text.lower():
            metadata["document_type"] = "Distribution"
        elif "adjustment" in text.lower():
            metadata["document_type"] = "Adjustment"
        elif "financial report" in text.lower():
            metadata["document_type"] = "Financial Report"
        date_match = re.search(r"\d{4}-\d{2}-\d{2}", text)
        if date_match:
            metadata["date"] = date_match.group(0)
        return metadata

    # ----------------------------------------------------------------------
    # 💾 SAVE TO DATABASE — PERBAIKAN UTAMA DI SINI
    # ----------------------------------------------------------------------
    def _save_to_db(self, db: Session, document_id: int, meta: dict, tables: List[dict]):
        doc = db.query(DBDocument).filter(DBDocument.id == document_id).first()
        if not doc:
            raise ValueError(f"Document ID {document_id} not found")
        if not doc.fund_id:
            raise ValueError(f"Document ID {document_id} has no fund_id")
        fund_id = doc.fund_id

        for key, value in meta.items():
            if hasattr(doc, key):
                setattr(doc, key, value)
        db.commit()
        print(f"✅ Document metadata updated for ID {document_id}")

        for table in tables:
            t_type, rows = table["type"], table["data"]
            model_class = {
                "capital_calls": CapitalCall,
                "distributions": Distribution,
                "adjustments": Adjustment,
            }.get(t_type)
            if not model_class:
                print(f"⚠️ Unknown table type '{t_type}', skipping.")
                continue
            for row in rows:
                # === PERBAIKAN: Improved amount detection ===
                amount_val = 0.0
                amount_key = None
                for key in row.keys():
                    if "amount" in str(key).lower():
                        amount_key = key
                        break
                raw_amount = row.get(amount_key) if amount_key else None
                if raw_amount is not None and raw_amount != "":
                    try:
                        clean = re.sub(r'[^\d\.\-]', '', str(raw_amount))
                        amount_val = float(clean)
                    except Exception as e:
                        print(f"⚠️ Error parsing amount '{raw_amount}': {e}")
                        amount_val = 0.0
                # ===========================================
                desc = str(row.get("Description", ""))[:500]
                # === PERBAIKAN: Flexible date detection ===
                date_key = None
                date_candidates = ["date", "due date", "distribution date", "adjustment date"]
                for key in row.keys():
                    if str(key).lower().strip() in date_candidates:
                        date_key = key
                        break
                date_val = row.get(date_key) if date_key else None
                # ===========================================
                try:
                    if date_val:
                        parsed_date = datetime.strptime(str(date_val).strip(), "%Y-%m-%d").date()
                    else:
                        parsed_date = datetime.now().date()
                except Exception:
                    parsed_date = datetime.now().date()

                # --- PERBAIKAN UTAMA: Tangani Recallable Distribution di tabel Distributions ---
                if t_type == "distributions":
                    # Periksa kolom "Recallable" atau "Type" untuk menentukan is_recallable
                    is_recallable_val = str(row.get("Recallable", "")).lower().strip()
                    type_val = str(row.get("Type", "")).lower().strip()
                    is_recallable_flag = (is_recallable_val == "yes" or is_recallable_val == "y" or is_recallable_val == "true" or "recallable" in type_val)

                    kwargs = {
                        "document_id": document_id,
                        "fund_id": fund_id,
                        "amount": amount_val,
                        "description": desc,
                        "distribution_date": parsed_date,
                        "is_recallable": is_recallable_flag
                    }
                    db.add(model_class(**kwargs))
                elif t_type == "capital_calls":
                    kwargs = {
                        "document_id": document_id,
                        "fund_id": fund_id,
                        "amount": amount_val,
                        "description": desc,
                        "call_date": parsed_date
                    }
                    db.add(model_class(**kwargs))
                elif t_type == "adjustments":
                    # Ambil adjustment_type dari kolom "Type" di baris
                    adj_type = str(row.get("Type", "")).lower().strip()
                    adj_type_mapped = "Other Adjustment" # Default
                    if "recallable" in adj_type:
                        adj_type_mapped = "Recallable Distribution"
                    elif "capital call adj" in adj_type:
                        adj_type_mapped = "Capital Call Adjustment"
                    elif "contribution adj" in adj_type or "expense" in adj_type:
                        adj_type_mapped = "Contribution Adjustment"
                    # Tambahkan mapping lain jika perlu

                    kwargs = {
                        "document_id": document_id,
                        "fund_id": fund_id,
                        "amount": amount_val, # Simpan nilai asli (bisa positif atau negatif)
                        "description": desc,
                        "adjustment_date": parsed_date,
                        "adjustment_type": adj_type_mapped
                    }
                    db.add(model_class(**kwargs))
            db.commit()
            print(f"💾 Inserted rows into '{t_type}'")
        print(f"✅ All data committed for document ID {document_id}")

    # ----------------------------------------------------------------------
    # 🔒 HELPER: Fund ID from path/filename — DIHAPUS LOGIKA OTOMATISNYA
    # ----------------------------------------------------------------------
    def _get_fund_id_from_path(self, db: Session, file_path: str) -> int:
        # Tidak digunakan lagi — fund_id harus dikirim eksplisit
        return None

    def _get_fund_id_from_filename(self, db: Session, filename: str) -> int:
        # Tidak digunakan lagi — fund_id harus dikirim eksplisit
        return None