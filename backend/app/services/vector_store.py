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
import json # Import json untuk konversi metadata
from sqlalchemy.orm import Session
from sqlalchemy import text, insert, select
# Ganti import ini:
# from langchain_openai import OpenAIEmbeddings
# from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings # <-- Tambahkan ini untuk fallback lokal
from app.core.config import settings
from app.db.session import SessionLocal
from sqlalchemy.sql import table, column
from sqlalchemy import Integer, String, Text, JSON


class VectorStore:
    """pgvector-based vector store for document embeddings"""

    # Dimensi default berdasarkan model embedding yang umum
    # Google: models/embedding-001 -> 768, models/text-embedding-004 -> 768
    # OpenAI: text-embedding-3-small -> 1536, text-embedding-ada-002 -> 1536
    # Sentence Transformers: all-MiniLM-L6-v2 -> 384, all-mpnet-base-v2 -> 768, BAAI/bge-large-en-v1.5 -> 1024
    _DEFAULT_DIMENSIONS = {
        "models/embedding-001": 768,
        "models/text-embedding-004": 768, # <-- Tambahkan dimensi untuk model baru
        # Tambahkan model lain jika diperlukan
    }

    def __init__(self, db: Session = None):
        self.db = db or SessionLocal()
        self.embeddings = self._initialize_embeddings() # Gunakan hasil inisialisasi
        self.embedding_dimension = self._get_embedding_dimension() # Simpan dimensi
        # Definisikan tabel SQLAlchemy Core untuk insert/select (opsional, untuk referensi)
        # self.document_embeddings_table = table('document_embeddings',
        #     column('id', Integer),
        #     column('document_id', Integer),
        #     column('fund_id', Integer),
        #     column('content', Text),
        #     column('embedding'),
        #     column('metadata', JSON)
        # )
        self._ensure_extension()

    def _initialize_embeddings(self):
        """Initialize embedding model based on settings."""
        # Periksa apakah penggunaan model lokal diaktifkan
        if settings.USE_LOCAL_EMBEDDINGS: # <-- Gunakan variabel konfigurasi
            print("Using Local HuggingFace Embeddings")
            # Gunakan model lokal yang ditentukan di konfigurasi
            return HuggingFaceEmbeddings(model_name=settings.LOCAL_EMBEDDING_MODEL)
        else:
            # Gunakan Google Embedding
            if not settings.GOOGLE_API_KEY:
                raise ValueError("GOOGLE_API_KEY is required for Google embeddings. Please set it in .env or set USE_LOCAL_EMBEDDINGS=True")
            print("Using Google Generative AI Embeddings")
            # Pastikan nama model Google benar (harus diawali models/)
            return GoogleGenerativeAIEmbeddings(
                model=settings.GEMINI_EMBEDDING_MODEL, # Pastikan ini adalah "models/text-embedding-004" atau "models/embedding-001"
                google_api_key=settings.GOOGLE_API_KEY
            )

    def _get_embedding_dimension(self) -> int:
        """
        Mendapatkan dimensi embedding dari model yang digunakan.
        Jika model tidak dikenal, coba deteksi dari tabel database atau gunakan default.
        """
        # Cek model Google terlebih dahulu
        model_name = getattr(self.embeddings, "model", None) # Untuk Google
        if model_name and model_name in self._DEFAULT_DIMENSIONS:
            dim = self._DEFAULT_DIMENSIONS[model_name]
            print(f"Detected embedding dimension {dim} for model {model_name}")
            return dim

        # Cek model HuggingFace
        hf_model_name = getattr(self.embeddings, "model_name", None) # Untuk HuggingFace
        if hf_model_name:
            # Mapping dimensi umum untuk model HuggingFace lokal
            hf_dimensions = {
                "sentence-transformers/all-MiniLM-L6-v2": 384,
                "sentence-transformers/all-MiniLM-L12-v2": 384,
                "sentence-transformers/all-mpnet-base-v2": 768,
                "BAAI/bge-small-en-v1.5": 384,
                "BAAI/bge-base-en-v1.5": 768,
                "BAAI/bge-large-en-v1.5": 1024, # <-- Tambahkan dimensi untuk model Anda
                # Tambahkan model lain jika diperlukan
            }
            if hf_model_name in hf_dimensions:
                dim = hf_dimensions[hf_model_name]
                print(f"Detected embedding dimension {dim} for HuggingFace model {hf_model_name}")
                return dim

        # Fallback: Coba deteksi dari tabel jika sudah ada (kompleks, dihindari dulu)
        # Gunakan default atau raise exception
        # Disini kita asumsikan model Google (768) sebagai default jika tidak bisa dideteksi.
        # Atau, kita bisa raise error jika model tidak dikenal.
        print(f"Warning: Could not determine embedding dimension for model {model_name or hf_model_name}. Using default based on configuration.")
        # Kita bisa menentukan default berdasarkan konfigurasi
        if settings.USE_LOCAL_EMBEDDINGS:
            # Default jika menggunakan model lokal dan tidak dikenal
            # Ambil dari mapping default di atas atau tetapkan default
            # Misalnya, untuk BAAI/bge-large-en-v1.5, defaultnya adalah 1024
            # Kita bisa tambahkan logika untuk menentukan default jika model_name tidak dikenal
            # Untuk sementara, gunakan default yang umum untuk model besar jika LOCAL_EMBEDDING_MODEL adalah yang besar
            if "bge-large" in settings.LOCAL_EMBEDDING_MODEL:
                 return 1024
            elif "bge-base" in settings.LOCAL_EMBEDDING_MODEL:
                 return 768
            elif "all-mpnet" in settings.LOCAL_EMBEDDING_MODEL:
                 return 768
            elif "all-MiniLM" in settings.LOCAL_EMBEDDING_MODEL:
                 return 384
            else:
                 print("Using default dimension 768 for local embeddings (unknown specific model).")
                 return 768
        else:
             print("Using default dimension 768 for Google embeddings (unknown specific model).")
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
            dimension = self.embedding_dimension # Gunakan dimensi yang sudah dihitung di __init__
            print(f"Using embedding dimension: {dimension}") # Log untuk debugging

            # Create embeddings table
            # Gunakan f-string untuk menyisipkan dimensi ke dalam definisi tabel
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
            print("Vector store table ensured.")
        except Exception as e:
            print(f"Error ensuring pgvector extension or table: {e}")
            self.db.rollback()
            raise # Re-raise untuk menghentikan proses jika gagal

    async def add_document(self, content: str, metadata: Dict[str, Any]): # <-- GANTI NAMA PARAMETER DARI 'meta' MENJADI 'metadata'
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

            # Convert embedding list to string for pgvector
            embedding_str = "[" + ",".join(str(float(x)) for x in embedding) + "]"

            # --- PERBAIKAN: Konversi metadata dict ke string JSON ---
            # PostgreSQL kolom JSONB mengharapkan string JSON.
            # SQLAlchemy biasanya menanganinya jika kolomnya didefinisikan dengan tipe JSON/JSONB di model,
            # tetapi karena kita menggunakan text() dan raw SQL, kita harus konversi manual.
            metadata_json_str = json.dumps(metadata) # <-- GANTI 'meta' MENJADI 'metadata'
            # --------------------------------------------------------

            # --- PENDEKATAN YANG DIPERBAIKI: Gunakan text() dan session.execute() ---
            # dengan placeholder :nama (hanya satu gaya placeholder)
            # Kita masukkan string embedding sebagai parameter juga, bukan casting di dalam VALUES.
            # Casting ::vector akan diterapkan oleh PostgreSQL saat insert ke kolom bertipe vector.
            # Jadi, kita kirim string embedding ke parameter :embedding.
            insert_sql_raw = """
                INSERT INTO document_embeddings (document_id, fund_id, content, embedding, metadata)
                VALUES (:document_id, :fund_id, :content, :embedding, :metadata)
            """

            # Buat objek text() hanya dari string SQL mentah
            insert_sql = text(insert_sql_raw)

            # Gunakan session.execute() dengan statement dan parameter dictionary
            # Gunakan gaya :nama untuk SEMUA parameter
            # Pastikan semua placeholder di SQL memiliki pasangan di dictionary ini.
            self.db.execute(insert_sql, {
                "document_id": metadata.get("document_id"), # <-- GANTI 'meta' MENJADI 'metadata'
                "fund_id": metadata.get("fund_id"),         # <-- GANTI 'meta' MENJADI 'metadata'
                "content": content,
                "embedding": embedding_str, # <-- Kirim string embedding ke parameter :embedding
                "metadata": metadata_json_str        # <-- Kirim string JSON metadata ke parameter :metadata
            })
            # --- AKHIR PENDEKATAN YANG DIPERBAIKI ---

            self.db.commit()
            print(f"Document added successfully with metadata {metadata}") # <-- GANTI 'meta' MENJADI 'metadata'
        except Exception as e:
            print(f"Error adding document: {e}")
            # Cetak statement SQL yang bermasalah untuk debugging (opsional, jangan di-production)
            # print(f"SQL Statement that failed: {insert_sql_raw if 'insert_sql_raw' in locals() else 'N/A'}")
            # print(f"Parameters that failed: {params if 'params' in locals() else 'N/A'}")
            self.db.rollback()
            raise # Re-raise agar error bisa ditangani oleh pemanggil

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
            # Generate query embedding
            query_embedding = await self._get_embedding(query)
            # Convert to the same string format used in add_document
            query_embedding_str = "[" + ",".join(str(float(x)) for x in query_embedding) + "]"

            # Build WHERE clause for filtering
            where_conditions = []
            if filter_metadata:
                if "fund_id" in filter_metadata:
                    where_conditions.append(f"fund_id = {filter_metadata['fund_id']}")
                if "document_id" in filter_metadata:
                    where_conditions.append(f"document_id = {filter_metadata['document_id']}")
            
            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""

            # Use f-string to directly insert the stringified embedding and k into the SQL
            # This avoids placeholder escaping issues entirely.
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
            # Ganti raise dengan return array kosong atau nilai default jika gagal
            # agar proses tidak berhenti total (opsional, tergantung kebijakan error handling)
            # raise
            print("Returning zero vector due to embedding error.")
            return np.zeros(self.embedding_dimension, dtype=np.float32) # Atau sesuaikan

        return np.array(embedding, dtype=np.float32)

    def clear(self, fund_id: Optional[int] = None):
        """
        Clear the vector store

        TODO: Implement this method
        - Delete all embeddings (or filter by fund_id)
        """
        try:
            if fund_id:
                # Gunakan placeholder :nama
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
