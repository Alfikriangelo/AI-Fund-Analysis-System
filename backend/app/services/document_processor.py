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

from docling.document_converter import DocumentConverter
from docling_core.types import DoclingDocument
from docling_core.types.doc import TableItem

from app.models.fund import Fund
from app.models.document import Document as DBDocument
from app.models.transaction import CapitalCall, Distribution, Adjustment
from app.db.session import SessionLocal
from app.core.config import settings
from app.services.vector_store import VectorStore
from sqlalchemy.orm import Session


class DocumentProcessor:

    def __init__(self):
        self.converter = DocumentConverter()
        self.vector_store = VectorStore()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            length_function=len,
        )

    async def process_document(self, file_path: str, document_id: int, fund_id: int) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            
            if not fund_id:
                raise ValueError("❌ Fund ID is required. Please specify fund_id during upload.")

            conversion_result = self.converter.convert(file_path)
            if not hasattr(conversion_result, "document"):
                raise ValueError("Docling conversion did not produce a document object.")
            doc: DoclingDocument = conversion_result.document
            self._inspect_doc_structure(doc)

            text = self._extract_text_from_doc(doc)

            metadata = self._extract_metadata(text, file_path)

            tables = self._extract_tables_from_doc(doc)

            doc_db = db.query(DBDocument).filter(DBDocument.id == document_id).first()
            if not doc_db:
                raise ValueError(f"Document ID {document_id} not found")
            if not doc_db.fund_id:
                doc_db.fund_id = fund_id
                db.commit()

            self._save_to_db(db, document_id, metadata, tables)

            await self._save_text_to_vector_store(text, document_id, fund_id)

            return {"status": "completed"}

        except Exception as e:
            traceback.print_exc()
            return {"status": "failed", "error": str(e)}
        finally:
            db.close()

    def _inspect_doc_structure(self, doc: DoclingDocument):
        try:
            attrs = [a for a in dir(doc) if not a.startswith("_")]
            if hasattr(doc, "tables") and doc.tables:
                t = doc.tables[0]
                t_attrs = [a for a in dir(t) if not a.startswith("_")]
        except Exception as e:
            print(f"⚠️ Docling: Inspection failed: {e}")

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

    async def _save_text_to_vector_store(self, text: str, document_id: int, fund_id: int):
        if not text.strip():
            return
        chunks = self.text_splitter.split_text(text)
        metadata = {
            "document_id": document_id,
            "fund_id": fund_id,
            "source_type": "pdf_text"
        }
        for i, chunk in enumerate(chunks):
            meta = {**metadata, "chunk_index": i}
            await self.vector_store.add_document(content=chunk, metadata=meta)

    def _extract_tables_from_doc(self, doc: DoclingDocument) -> List[dict]:
        tables = []
        if not hasattr(doc, "tables") or not doc.tables:
            return tables
        for i, table_item in enumerate(doc.tables):
            try:
                if not isinstance(table_item, TableItem):
                    continue
                df = table_item.export_to_dataframe()
                if df.empty:
                    continue
                normalized_columns = []
                for col in df.columns:
                    clean_col = str(col).strip().replace(" (USD)", "").replace("$", "").replace("*", "")
                    normalized_columns.append(clean_col)
                df.columns = normalized_columns
                headers = [str(c) for c in df.columns]
                header_text = " ".join(headers).lower()
                table_type = "Unknown"

                if "type" in [c.lower() for c in df.columns]:
                    type_values = " ".join(str(v).lower() for v in df["Type"].dropna().unique())
                    if "recallable dist" in type_values:
                        table_type = "adjustments"  
                    elif "return" in type_values or "income" in type_values:
                        table_type = "distributions"
                    elif "capital call adj" in type_values or "contribution adjustment" in type_values:
                        table_type = "adjustments"
                    elif "call" in type_values:
                        table_type = "capital_calls"
                if table_type == "Unknown":
                    if any(k in header_text for k in ["distrib", "payout", "return", "income"]):
                        table_type = "distributions"
                    elif any(k in header_text for k in ["adjust", "correction", "fee", "reclass"]):
                        table_type = "adjustments"
                    elif any(k in header_text for k in ["capital", "call", "called"]):
                        table_type = "capital_calls"
                if table_type == "Unknown":
                    fallback_types = ["capital_calls", "distributions", "adjustments"]
                    if i < len(fallback_types):
                        table_type = fallback_types[i]
                      
                tables.append({"type": table_type, "data": df.to_dict(orient="records")})
            except Exception as e:
                traceback.print_exc()
        return tables

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

        for table in tables:
            t_type, rows = table["type"], table["data"]
            model_class = {
                "capital_calls": CapitalCall,
                "distributions": Distribution,
                "adjustments": Adjustment,
            }.get(t_type)
            if not model_class:
                continue
            for row in rows:
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
                desc = str(row.get("Description", ""))[:500]
                date_key = None
                date_candidates = ["date", "due date", "distribution date", "adjustment date"]
                for key in row.keys():
                    if str(key).lower().strip() in date_candidates:
                        date_key = key
                        break
                date_val = row.get(date_key) if date_key else None
                try:
                    if date_val:
                        parsed_date = datetime.strptime(str(date_val).strip(), "%Y-%m-%d").date()
                    else:
                        parsed_date = datetime.now().date()
                except Exception:
                    parsed_date = datetime.now().date()

                if t_type == "distributions":
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
                    adj_type = str(row.get("Type", "")).lower().strip()
                    adj_type_mapped = "Other Adjustment" # Default
                    if "recallable" in adj_type:
                        adj_type_mapped = "Recallable Distribution"
                    elif "capital call adj" in adj_type:
                        adj_type_mapped = "Capital Call Adjustment"
                    elif "contribution adj" in adj_type or "expense" in adj_type:
                        adj_type_mapped = "Contribution Adjustment"

                    kwargs = {
                        "document_id": document_id,
                        "fund_id": fund_id,
                        "amount": amount_val,
                        "description": desc,
                        "adjustment_date": parsed_date,
                        "adjustment_type": adj_type_mapped
                    }
                    db.add(model_class(**kwargs))
            db.commit()


    def _get_fund_id_from_path(self, db: Session, file_path: str) -> int:
        return None

    def _get_fund_id_from_filename(self, db: Session, filename: str) -> int:
        return None