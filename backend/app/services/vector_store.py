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
from sqlalchemy.orm import Session
from sqlalchemy import text
# Ganti import ini:
# from langchain_openai import OpenAIEmbeddings
# from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings # Masih digunakan sebagai fallback
from app.core.config import settings
from app.db.session import SessionLocal


class VectorStore:
    """pgvector-based vector store for document embeddings"""

    # Dimensi default berdasarkan model embedding yang umum
    # Google: models/embedding-001 -> 768
    # OpenAI: text-embedding-3-small -> 1536, text-embedding-ada-002 -> 1536
    # Sentence Transformers: all-MiniLM-L6-v2 -> 384
    _DEFAULT_DIMENSIONS = {
        "models/embedding-001": 768,
        # Tambahkan model lain jika diperlukan
    }

    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()
        self.embeddings = self._initialize_embeddings()
        self._ensure_extension()

    def _initialize_embeddings(self):
        """Initialize embedding model"""
        if settings.GOOGLE_API_KEY: # <-- GANTI KONDISI
            print("Using Google Generative AI Embeddings") # Log untuk debugging
            return GoogleGenerativeAIEmbeddings( # <-- GANTI INISIALISASI
                model=settings.GEMINI_EMBEDDING_MODEL, # <-- GANTI NAMA MODEL
                google_api_key=settings.GOOGLE_API_KEY # <-- GANTI NAMA API KEY
            )
        else:
            # Fallback ke local embeddings
            print("Using HuggingFace Embeddings (Fallback)") # Log untuk debugging
            return HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )

    def _get_embedding_dimension(self) -> int:
        """
        Mendapatkan dimensi embedding dari model yang digunakan.
        Jika model tidak dikenal, coba deteksi dari tabel database.
        """
        model_name = getattr(self.embeddings, "model", None)
        if model_name and model_name in self._DEFAULT_DIMENSIONS:
            return self._DEFAULT_DIMENSIONS[model_name]

        # Fallback: Coba deteksi dari tabel jika sudah ada
        # Peringatan: Ini bisa gagal jika tabel kosong atau kolom embedding tidak bisa di-query
        # Solusi paling aman adalah menentukan dimensi berdasarkan model yang dikonfigurasi.
        # Karena HuggingFaceEmbeddings tidak selalu menyediakan cara mudah untuk mendapatkan dimensi,
        # kita asumsikan dimensi default untuk model fallback.
        if "all-MiniLM-L6-v2" in getattr(self.embeddings, "model_name", ""):
            return 384

        # Jika tidak bisa ditentukan, kembalikan default atau raise exception
        # Disini kita asumsikan model Google (768) sebagai default jika tidak ada yang lain.
        # Ini bisa disesuaikan.
        print(f"Warning: Could not determine embedding dimension for {model_name}. Using default.")
        return 768 # Default untuk Google Embedding Model jika tidak bisa dideteksi dari konfigurasi

    def _ensure_extension(self):
        """
        Ensure pgvector extension is enabled

        TODO: Implement this method
        - Execute: CREATE EXTENSION IF NOT EXISTS vector;
        - Create embeddings table if not exists
        """
        try:
            # Enable pgvector extension
            self.db.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            self.db.commit() # Commit perubahan extension

            # Dapatkan dimensi embedding dari model yang digunakan
            dimension = self._get_embedding_dimension()
            print(f"Using embedding dimension: {dimension}") # Log untuk debugging

            # Create embeddings table
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS document_embeddings (
                id SERIAL PRIMARY KEY,
                document_id INTEGER,
                fund_id INTEGER,
                content TEXT NOT NULL,
                embedding vector({dimension}),
                metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS document_embeddings_embedding_idx
            ON document_embeddings USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100);
            """

            self.db.execute(text(create_table_sql))
            self.db.commit()
            print("Vector store table ensured.")
        except Exception as e:
            print(f"Error ensuring pgvector extension or table: {e}")
            self.db.rollback()
            raise # Re-raise untuk menghentikan proses jika gagal

    async def add_document(self, content: str, metadata: Dict[str, Any]):
        """
        Add a document to the vector store

        TODO: Implement this method
        - Generate embedding for content
        - Insert into document_embeddings table
        - Store metadata as JSONB
        """
        try:
            # Generate embedding using the initialized self.embeddings
            embedding = await self._get_embedding(content)
            embedding_list = embedding.tolist()

            # Insert into database
            insert_sql = text("""
                INSERT INTO document_embeddings (document_id, fund_id, content, embedding, metadata)
                VALUES (:document_id, :fund_id, :content, :embedding::vector, :metadata::jsonb)
            """)

            self.db.execute(insert_sql, {
                "document_id": metadata.get("document_id"),
                "fund_id": metadata.get("fund_id"),
                "content": content,
                "embedding": str(embedding_list), # Convert list to string for pgvector
                "metadata": str(metadata) # Convert dict to string for JSONB
            })
            self.db.commit()
            print(f"Document added successfully with metadata: {metadata}")
        except Exception as e:
            print(f"Error adding document: {e}")
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

        TODO: Implement this method
        - Generate query embedding
        - Use pgvector's <=> operator for cosine distance
        - Apply metadata filters if provided
        - Return top k results

        Args:
            query: Search query
            k: Number of results to return
            filter_metadata: Optional metadata filters (e.g., {"fund_id": 1})

        Returns:
            List of similar documents with scores
        """
        try:
            # Generate query embedding using the same self.embeddings
            query_embedding = await self._get_embedding(query)
            embedding_list = query_embedding.tolist()

            # Build query with optional filters
            where_clause = ""
            params = {"query_embedding": str(embedding_list), "k": k}
            if filter_metadata:
                conditions = []
                for key, value in filter_metadata.items():
                    if key in ["document_id", "fund_id"]:
                        conditions.append(f"{key} = :{key}")
                        params[key] = value
                if conditions:
                    where_clause = "WHERE " + " AND ".join(conditions)

            # Search using cosine distance (<=> operator)
            # Score is calculated as 1 - distance (so higher is more similar)
            search_sql = text(f"""
                SELECT
                    id,
                    document_id,
                    fund_id,
                    content,
                    metadata,
                    1 - (embedding <=> :query_embedding::vector) as similarity_score
                FROM document_embeddings
                {where_clause}
                ORDER BY embedding <=> :query_embedding::vector
                LIMIT :k
            """)

            result = self.db.execute(search_sql, params)

            # Format results
            results = []
            for row in result:
                results.append({
                    "id": row[0],
                    "document_id": row[1],
                    "fund_id": row[2],
                    "content": row[3],
                    "metadata": row[4], # row[4] adalah metadata JSONB, bisa langsung di-return
                    "score": float(row[5]) # row[5] adalah similarity_score
                })

            print(f"Similarity search returned {len(results)} results.")
            return results
        except Exception as e:
            print(f"Error in similarity search: {e}")
            return []

    async def _get_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for text using the initialized self.embeddings."""
        try:
            # Gunakan embed_query jika tersedia (untuk OpenAI, Google)
            # atau encode jika tidak (untuk HuggingFace)
            if hasattr(self.embeddings, 'embed_query'):
                embedding = self.embeddings.embed_query(text)
            elif hasattr(self.embeddings, 'encode'):
                embedding = self.embeddings.encode(text)
            else:
                raise AttributeError(f"Embedding model {type(self.embeddings)} has no 'embed_query' or 'encode' method.")
        except Exception as e:
            print(f"Error generating embedding: {e}")
            raise # Re-raise agar error bisa ditangani oleh fungsi pemanggil

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
                print(f"Cleared embeddings for fund_id: {fund_id}")
            else:
                delete_sql = text("DELETE FROM document_embeddings")
                self.db.execute(delete_sql)
                print("Cleared all embeddings from vector store.")

            self.db.commit()
        except Exception as e:
            print(f"Error clearing vector store: {e}")
            self.db.rollback()
