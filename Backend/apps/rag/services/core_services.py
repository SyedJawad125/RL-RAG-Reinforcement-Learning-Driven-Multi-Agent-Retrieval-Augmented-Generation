# rag/services/core_services.py
"""
Core Services for Multi-Agent RAG System
Includes LLM, Embeddings, and ChromaDB Vector Store
"""
import logging
from typing import List, Dict, Any, Optional
import numpy as np
from django.conf import settings
from sentence_transformers import SentenceTransformer
from groq import AsyncGroq
import chromadb
from chromadb.config import Settings as ChromaSettings

logger = logging.getLogger(__name__)


# ============================================
# LLM Service (Groq)
# ============================================

class LLMService:
    """LLM Service using Groq API with async support."""
    
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model or settings.GROQ_MODEL
        
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not configured")
        
        self.client = AsyncGroq(api_key=self.api_key)
        logger.info(f"[LLMService] Initialized with model: {self.model}")
    
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 1000,
        system_prompt: Optional[str] = None
    ) -> str:
        """Generate text using Groq LLM."""
        try:
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            messages.append({"role": "user", "content": prompt})
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"[LLMService] Generation failed: {e}")
            raise


# ============================================
# Embedding Service
# ============================================

class EmbeddingService:
    """Embedding service using sentence-transformers."""
    
    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL
        logger.info(f"[EmbeddingService] Loading model: {self.model_name}")
        
        self.model = SentenceTransformer(self.model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        
        logger.info(f"[EmbeddingService] Model loaded (dimension: {self.dimension})")
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"[EmbeddingService] Single embedding failed: {e}")
            raise
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts (batch)."""
        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=len(texts) > 10)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"[EmbeddingService] Batch embedding failed: {e}")
            raise
    
    def get_dimension(self) -> int:
        """Get embedding dimension"""
        return self.dimension


# ============================================
# ChromaDB Vector Store
# ============================================

class ChromaDBVectorStore:
    """ChromaDB-based vector store for document chunks."""
    
    def __init__(self, collection_name: str = None, persist_directory: str = None):
        self.collection_name = collection_name or settings.CHROMADB_COLLECTION_NAME
        self.persist_directory = str(persist_directory or settings.CHROMADB_PERSIST_DIR)
        
        logger.info(f"[ChromaDB] Initializing with directory: {self.persist_directory}")
        
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=ChromaSettings(anonymized_telemetry=False, allow_reset=True)
        )
        
        try:
            self.collection = self.client.get_collection(name=self.collection_name)
            logger.info(f"[ChromaDB] Using existing collection: {self.collection_name}")
        except:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"[ChromaDB] Created new collection: {self.collection_name}")
    
    def add_documents(self, documents: List[str], embeddings: List[List[float]], metadata: List[Dict[str, Any]], ids: List[str]):
        """Add documents to ChromaDB."""
        try:
            self.collection.add(documents=documents, embeddings=embeddings, metadatas=metadata, ids=ids)
            logger.info(f"[ChromaDB] Added {len(documents)} documents")
        except Exception as e:
            logger.error(f"[ChromaDB] Failed to add documents: {e}")
            raise
    
    def search(self, query_embedding: List[float], top_k: int = 5, filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        try:
            query_params = {"query_embeddings": [query_embedding], "n_results": top_k}
            if filter:
                query_params["where"] = filter
            
            results = self.collection.query(**query_params)
            
            formatted_results = []
            if results and results["documents"] and results["documents"][0]:
                for i in range(len(results["documents"][0])):
                    formatted_results.append({
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "score": 1 - results["distances"][0][i] if results["distances"] else 0.0,
                        "distance": results["distances"][0][i] if results["distances"] else 0.0
                    })
            
            return formatted_results
        except Exception as e:
            logger.error(f"[ChromaDB] Search failed: {e}")
            return []
    
    def get_count(self) -> int:
        """Get number of documents in collection"""
        try:
            return self.collection.count()
        except Exception as e:
            logger.error(f"[ChromaDB] Failed to get count: {e}")
            return 0
    
    def reset_collection(self):
        """Reset (clear) the collection"""
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(name=self.collection_name, metadata={"hnsw:space": "cosine"})
            logger.info(f"[ChromaDB] Collection reset: {self.collection_name}")
        except Exception as e:
            logger.error(f"[ChromaDB] Failed to reset collection: {e}")
            raise
    
    def delete_by_document_id(self, document_id: str):
        """Delete all chunks for a specific document."""
        try:
            self.collection.delete(where={"document_id": document_id})
            logger.info(f"[ChromaDB] Deleted chunks for document: {document_id}")
        except Exception as e:
            logger.error(f"[ChromaDB] Failed to delete document chunks: {e}")
            raise


# ============================================
# Service Singletons
# ============================================

_llm_service_instance = None
_embedding_service_instance = None
_vector_store_instance = None


def get_llm_service() -> LLMService:
    """Get or create LLM service singleton"""
    global _llm_service_instance
    if _llm_service_instance is None:
        _llm_service_instance = LLMService()
    return _llm_service_instance


def get_embedding_service() -> EmbeddingService:
    """Get or create embedding service singleton"""
    global _embedding_service_instance
    if _embedding_service_instance is None:
        _embedding_service_instance = EmbeddingService()
    return _embedding_service_instance


def get_vector_store() -> ChromaDBVectorStore:
    """Get or create vector store singleton"""
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = ChromaDBVectorStore()
    return _vector_store_instance


def initialize_services():
    """Initialize all services (call on startup)"""
    logger.info("[Services] Initializing all services...")
    get_llm_service()
    get_embedding_service()
    get_vector_store()
    logger.info("[Services] All services initialized successfully")



import os
import re
import csv
import json
import hashlib
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field


# ─────────────────────────────────────────────────────────────────────────────
#  DATA STRUCTURES
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Document:
    """A single indexable unit for ChromaDB / any vector store."""
    text: str                          # Natural language text to embed
    metadata: Dict[str, Any]           # Filterable fields
    doc_id: str                        # Unique ID
    source_file: str                   # Original filename
    chunk_index: int = 0              # Position within file
    row_index: Optional[int] = None   # For tabular data: which row


@dataclass
class ProcessingResult:
    """Result returned after processing any file."""
    documents: List[Document]
    file_type: str
    total_rows: int
    columns_detected: List[str]
    warnings: List[str] = field(default_factory=list)



# ─────────────────────────────────────────────────────────────────────────────
#  STEP 5 — CHROMADB INDEXER (Generic — uses document metadata automatically)
# ─────────────────────────────────────────────────────────────────────────────

class GenericChromaIndexer:
    """
    Indexes any processed documents into ChromaDB.
    Metadata is stored automatically — no hardcoding.
    """

    def __init__(self, collection_name: str = "rag_collection"):
        self.collection_name = collection_name
        self._collection = None

    def get_collection(self):
        """Lazy init — only import chromadb when needed."""
        if self._collection is None:
            import chromadb
            client = chromadb.PersistentClient(path="./chroma_db")
            self._collection = client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        return self._collection

    def index_documents(self, result: ProcessingResult, batch_size: int = 100):
        """Index all documents from a ProcessingResult into ChromaDB."""
        collection = self.get_collection()
        documents = result.documents

        print(f"\n🔗 Indexing {len(documents)} documents...")

        # Sanitize metadata — ChromaDB only accepts str, int, float, bool
        def sanitize_meta(meta: Dict) -> Dict:
            clean = {}
            for k, v in meta.items():
                if isinstance(v, (str, int, float, bool)):
                    clean[str(k)] = v
                else:
                    clean[str(k)] = str(v)
            return clean

        # Batch insert
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            collection.upsert(
                ids=[doc.doc_id for doc in batch],
                documents=[doc.text for doc in batch],
                metadatas=[sanitize_meta(doc.metadata) for doc in batch],
            )
            print(f"   Indexed batch {i // batch_size + 1} / {(len(documents) - 1) // batch_size + 1}")

        print(f"✅ Indexed {len(documents)} documents into '{self.collection_name}'")

    def query(
        self, 
        query_text: str, 
        top_k: int = 5,
        filter_file: Optional[str] = None
    ) -> List[Dict]:
        """
        Generic query — works regardless of what files were indexed.
        Optional: filter results to a specific source file.
        """
        collection = self.get_collection()
        
        where_clause = None
        if filter_file:
            where_clause = {"source_file": {"$eq": filter_file}}

        results = collection.query(
            query_texts=[query_text],
            n_results=top_k,
            where=where_clause,
            include=["documents", "metadatas", "distances"]
        )

        output = []
        if results and results["documents"]:
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0]
            ):
                output.append({
                    "text": doc,
                    "metadata": meta,
                    "relevance_score": round(1 - dist, 4)
                })
        return output