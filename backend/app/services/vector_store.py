"""
Vector store service using pgvector (PostgreSQL extension)

TODO: Implement vector storage using pgvector
- Create embeddings table in PostgreSQL
- Store document chunks with vector embeddings
- Implement similarity search using pgvector operators
- Handle metadata filtering
"""
from typing import List, Dict, Any, Optional
import numpy as np
import json 
from sqlalchemy.orm import Session
from sqlalchemy import text, insert, select
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings 
from app.core.config import settings
from app.db.session import SessionLocal
from sqlalchemy.sql import table, column
from sqlalchemy import Integer, String, Text, JSON


class VectorStore:
    """pgvector-based vector store for document embeddings"""

    _DEFAULT_DIMENSIONS = {
        "models/embedding-001": 768,
        "models/text-embedding-004": 768, 
    }

    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()
        self.embeddings = self._initialize_embeddings() 
        self.embedding_dimension = self._get_embedding_dimension() 
        self._ensure_extension()

    def _initialize_embeddings(self):
        """Initialize embedding model based on settings."""
        if settings.USE_LOCAL_EMBEDDINGS: 
            return HuggingFaceEmbeddings(model_name=settings.LOCAL_EMBEDDING_MODEL)
        else:
            if not settings.GOOGLE_API_KEY:
                raise ValueError("GOOGLE_API_KEY is required for Google embeddings. Please set it in .env or set USE_LOCAL_EMBEDDINGS=True")
            return GoogleGenerativeAIEmbeddings(
                model=settings.GEMINI_EMBEDDING_MODEL, 
                google_api_key=settings.GOOGLE_API_KEY
            )

    def _get_embedding_dimension(self) -> int:

        model_name = getattr(self.embeddings, "model", None) 
        if model_name and model_name in self._DEFAULT_DIMENSIONS:
            dim = self._DEFAULT_DIMENSIONS[model_name]
            return dim

        hf_model_name = getattr(self.embeddings, "model_name", None) 
        if hf_model_name:
            hf_dimensions = {
                "sentence-transformers/all-MiniLM-L6-v2": 384,
                "sentence-transformers/all-MiniLM-L12-v2": 384,
                "sentence-transformers/all-mpnet-base-v2": 768,
                "BAAI/bge-small-en-v1.5": 384,
                "BAAI/bge-base-en-v1.5": 768,
                "BAAI/bge-large-en-v1.5": 1024,
            }
            if hf_model_name in hf_dimensions:
                dim = hf_dimensions[hf_model_name]
                return dim

        if settings.USE_LOCAL_EMBEDDINGS:
            if "bge-large" in settings.LOCAL_EMBEDDING_MODEL:
                 return 1024
            elif "bge-base" in settings.LOCAL_EMBEDDING_MODEL:
                 return 768
            elif "all-mpnet" in settings.LOCAL_EMBEDDING_MODEL:
                 return 768
            elif "all-MiniLM" in settings.LOCAL_EMBEDDING_MODEL:
                 return 384
            else:
                 return 768
        else:
             return 768 

    def _ensure_extension(self):
        """
        Ensure pgvector extension is enabled

        TODO: Implement this method
        - Execute: CREATE EXTENSION IF NOT EXISTS vector;
        - Create embeddings table if not exists
        """
        try:
            self.db.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            self.db.commit()

            dimension = self.embedding_dimension 

            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS document_embeddings (
                id SERIAL PRIMARY KEY,
                document_id INTEGER,
                fund_id INTEGER,
                content TEXT NOT NULL,
                embedding vector({dimension}), -- Dimensi disisipkan di sini
                metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS document_embeddings_embedding_idx
            ON document_embeddings USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100);
            """

            self.db.execute(text(create_table_sql))
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise 

    async def add_document(self, content: str, metadata: Dict[str, Any]):
        """
        Add a document to the vector store

        TODO: Implement this method
        - Generate embedding for content
        - Insert into document_embeddings table
        - Store metadata as JSONB
        """
        try:
            embedding = await self._get_embedding(content)
            embedding_list = embedding.tolist()

            embedding_str = "[" + ",".join(str(float(x)) for x in embedding) + "]"

            metadata_json_str = json.dumps(metadata) 
  
            insert_sql_raw = """
                INSERT INTO document_embeddings (document_id, fund_id, content, embedding, metadata)
                VALUES (:document_id, :fund_id, :content, :embedding, :metadata)
            """

            insert_sql = text(insert_sql_raw)

            self.db.execute(insert_sql, {
                "document_id": metadata.get("document_id"),
                "fund_id": metadata.get("fund_id"),  
                "content": content,
                "embedding": embedding_str,
                "metadata": metadata_json_str
            })

            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise 

    async def similarity_search(
        self,
        query: str,
        k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents using cosine similarity
        """
        try:
            query_embedding = await self._get_embedding(query)
            query_embedding_str = "[" + ",".join(str(float(x)) for x in query_embedding) + "]"

            where_conditions = []
            if filter_metadata:
                if "fund_id" in filter_metadata:
                    where_conditions.append(f"fund_id = {filter_metadata['fund_id']}")
                if "document_id" in filter_metadata:
                    where_conditions.append(f"document_id = {filter_metadata['document_id']}")
            
            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""

            search_sql = f"""
                SELECT
                    id,
                    document_id,
                    fund_id,
                    content,
                    metadata,
                    1 - (embedding <=> '{query_embedding_str}'::vector) as similarity_score
                FROM document_embeddings
                {where_clause}
                ORDER BY embedding <=> '{query_embedding_str}'::vector
                LIMIT {k}
            """

            result = self.db.execute(text(search_sql))
            results = []
            for row in result:
                results.append({
                    "id": row[0],
                    "document_id": row[1],
                    "fund_id": row[2],
                    "content": row[3],
                    "metadata": row[4],
                    "score": float(row[5])
                })

            return results
        except Exception as e:
            return []

    async def _get_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for text using the initialized self.embeddings."""
        try:
            if hasattr(self.embeddings, 'embed_query'):
                embedding = self.embeddings.embed_query(text)
            elif hasattr(self.embeddings, 'encode'):
                embedding = self.embeddings.encode(text)
            else:
                raise AttributeError(f"Embedding model {type(self.embeddings)} has no 'embed_query' or 'encode' method.")
        except Exception as e:
            return np.zeros(self.embedding_dimension, dtype=np.float32) 

        return np.array(embedding, dtype=np.float32)

    def clear(self, fund_id: Optional[int] = None):
        """
        Clear the vector store

        TODO: Implement this method
        - Delete all embeddings (or filter by fund_id)
        """
        try:
            if fund_id:
                delete_sql = text("DELETE FROM document_embeddings WHERE fund_id = :fund_id")
                self.db.execute(delete_sql, {"fund_id": fund_id})
            else:
                delete_sql = text("DELETE FROM document_embeddings")
                self.db.execute(delete_sql)

            self.db.commit()
        except Exception as e:
            self.db.rollback()
