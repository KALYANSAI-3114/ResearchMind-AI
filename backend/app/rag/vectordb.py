"""
Vector Database Module
Manage ChromaDB for storing and retrieving paper embeddings
"""

import chromadb
from chromadb.config import Settings
import os
from typing import List, Dict, Any


class VectorStore:
    """ChromaDB vector store for papers."""
    
    def __init__(self, db_path: str = "data/chroma_db"):
        """
        Initialize ChromaDB client.
        
        Args:
            db_path: Path to store ChromaDB files
        """
        os.makedirs(db_path, exist_ok=True)
        
        # Create persistent client
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = None
    
    def create_collection(self, collection_name: str) -> None:
        """
        Create or get a collection.
        
        Args:
            collection_name: Name of the collection
        """
        try:
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            raise Exception(f"Error creating collection: {str(e)}")
    
    def add_document(self, doc_id: str, text: str, embedding: List[float], 
                     metadata: Dict[str, Any] = None) -> None:
        """
        Add a document with embedding to the collection.
        
        Args:
            doc_id: Unique document ID
            text: Document text
            embedding: Embedding vector (as list)
            metadata: Additional metadata
        """
        if self.collection is None:
            raise ValueError("Collection not initialized")
        
        try:
            self.collection.add(
                ids=[doc_id],
                documents=[text],
                embeddings=[embedding],
                metadatas=[metadata or {}]
            )
        except Exception as e:
            raise Exception(f"Error adding document: {str(e)}")
    
    def add_documents_batch(self, doc_ids: List[str], texts: List[str], 
                            embeddings: List[List[float]], 
                            metadatas: List[Dict[str, Any]] = None) -> None:
        """
        Add multiple documents at once.
        
        Args:
            doc_ids: List of document IDs
            texts: List of document texts
            embeddings: List of embedding vectors
            metadatas: List of metadata dictionaries
        """
        if self.collection is None:
            raise ValueError("Collection not initialized")
        
        if metadatas is None:
            metadatas = [{} for _ in doc_ids]
        
        try:
            self.collection.add(
                ids=doc_ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas
            )
        except Exception as e:
            raise Exception(f"Error adding documents: {str(e)}")
    
    def query(self, embedding: List[float], n_results: int = 5) -> Dict[str, Any]:
        """
        Query similar documents.
        
        Args:
            embedding: Query embedding
            n_results: Number of results to return
        
        Returns:
            Query results
        """
        if self.collection is None:
            raise ValueError("Collection not initialized")
        
        try:
            results = self.collection.query(
                query_embeddings=[embedding],
                n_results=n_results
            )
            return results
        except Exception as e:
            raise Exception(f"Error querying collection: {str(e)}")
    
    def get_document(self, doc_id: str) -> Dict[str, Any]:
        """
        Get a specific document by ID.
        
        Args:
            doc_id: Document ID
        
        Returns:
            Document data
        """
        if self.collection is None:
            raise ValueError("Collection not initialized")
        
        try:
            results = self.collection.get(ids=[doc_id])
            return results
        except Exception as e:
            raise Exception(f"Error getting document: {str(e)}")
    
    def delete_document(self, doc_id: str) -> None:
        """
        Delete a document from collection.
        
        Args:
            doc_id: Document ID to delete
        """
        if self.collection is None:
            raise ValueError("Collection not initialized")
        
        try:
            self.collection.delete(ids=[doc_id])
        except Exception as e:
            raise Exception(f"Error deleting document: {str(e)}")
    
    def count_documents(self) -> int:
        """
        Get total number of documents in collection.
        
        Returns:
            Document count
        """
        if self.collection is None:
            raise ValueError("Collection not initialized")
        
        try:
            return self.collection.count()
        except Exception as e:
            raise Exception(f"Error counting documents: {str(e)}")


# Global vector store instance
vector_store = None


def initialize_vector_store(db_path: str = "data/chroma_db") -> VectorStore:
    """Initialize global vector store."""
    global vector_store
    vector_store = VectorStore(db_path)
    return vector_store


def get_vector_store() -> VectorStore:
    """Get the global vector store instance."""
    global vector_store
    if vector_store is None:
        vector_store = initialize_vector_store()
    return vector_store
