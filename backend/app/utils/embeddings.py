"""
Embeddings Module
Generate embeddings for text using sentence-transformers
"""

from sentence_transformers import SentenceTransformer
import numpy as np
import os
from typing import List


class EmbeddingGenerator:
    """Generate embeddings using open-source models."""

    def __init__(self, model_name: str = "BAAI/bge-small-en"):
        """
        Initialize the embedding model.

        Args:
            model_name: HuggingFace model name
        """
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name

    def encode_single(self, text: str) -> List[float]:
        """
        Encode a single text to embedding.

        Args:
            text: Text to encode

        Returns:
            Embedding as Python list
        """
        if not text or not isinstance(text, str):
            raise ValueError("Input must be a non-empty string")

        embedding = self.model.encode(text)

        return embedding.tolist()

    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Encode multiple texts to embeddings.

        Args:
            texts: List of texts to encode

        Returns:
            List of embedding vectors
        """
        if not texts or not all(isinstance(t, str) for t in texts):
            raise ValueError("Input must be a list of non-empty strings")

        embeddings = self.model.encode(texts)

        return embeddings.tolist()

    def similarity(self, text1: str, text2: str) -> float:
        """
        Calculate cosine similarity between two texts.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score (0-1)
        """
        from sklearn.metrics.pairwise import cosine_similarity

        emb1 = np.array(self.encode_single(text1))
        emb2 = np.array(self.encode_single(text2))

        similarity = cosine_similarity([emb1], [emb2])[0][0]

        return float(similarity)


# Global embedding generator instance
embedding_model_name = os.getenv("EMBEDDING_MODEL") or os.getenv("EMBED_MODEL") or "BAAI/bge-small-en"
embedding_generator = EmbeddingGenerator(embedding_model_name)


def create_embedding(text: str) -> List[float]:
    """
    Quick function to create embedding.

    Args:
        text: Text to encode

    Returns:
        Embedding vector
    """
    return embedding_generator.encode_single(text)


def create_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    Quick function to create embeddings for multiple texts.

    Args:
        texts: List of texts

    Returns:
        List of embeddings
    """
    return embedding_generator.encode_batch(texts)
