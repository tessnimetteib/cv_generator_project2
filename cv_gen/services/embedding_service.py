"""
Embedding Service
=================

Converts text to embeddings (vectors) using sentence-transformers.
Used for semantic similarity search in RAG.
"""

import numpy as np
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service for generating embeddings from text.
    
    Uses sentence-transformers 'all-MiniLM-L6-v2' model:
    - Fast (suitable for real-time applications)
    - Produces 384-dimensional vectors
    - Good semantic understanding
    - Lightweight and efficient
    """
    
    def __init__(self):
        """Initialize embedding model"""
        try:
            logger.info("Loading embedding model: all-MiniLM-L6-v2")
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("✅ Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"❌ Error loading embedding model: {e}")
            raise
    
    def generate_embedding(self, text):
        """
        Generate embedding for a single text.
        
        Args:
            text (str): Text to embed
            
        Returns:
            np.ndarray: 384-dimensional embedding vector
            
        Example:
            >>> service = EmbeddingService()
            >>> text = "Backend developer with 5 years experience"
            >>> embedding = service.generate_embedding(text)
            >>> embedding.shape
            (384,)
        """
        try:
            if not text or not isinstance(text, str):
                logger.warning(f"Invalid text input: {text}")
                return None
            
            # Clean text
            text = text.strip()
            
            if len(text) == 0:
                logger.warning("Empty text after stripping")
                return None
            
            # Generate embedding
            embedding = self.model.encode(text, convert_to_numpy=True)
            
            logger.debug(f"Generated embedding for text: {text[:50]}...")
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
    
    def generate_embeddings_batch(self, texts):
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts (list): List of texts to embed
            
        Returns:
            np.ndarray: Matrix of shape (n, 384)
            
        Example:
            >>> texts = ["Backend dev", "Frontend dev", "DevOps engineer"]
            >>> embeddings = service.generate_embeddings_batch(texts)
            >>> embeddings.shape
            (3, 384)
        """
        try:
            if not texts or not isinstance(texts, list):
                logger.warning("Invalid texts input")
                return None
            
            # Filter empty texts
            valid_texts = [t.strip() for t in texts if t and isinstance(t, str) and len(t.strip()) > 0]
            
            if not valid_texts:
                logger.warning("No valid texts to embed")
                return None
            
            logger.info(f"Generating embeddings for {len(valid_texts)} texts")
            embeddings = self.model.encode(valid_texts, convert_to_numpy=True)
            
            logger.debug(f"Generated {len(embeddings)} embeddings")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            return None
    
    def similarity(self, embedding1, embedding2):
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1 (np.ndarray): First embedding
            embedding2 (np.ndarray): Second embedding
            
        Returns:
            float: Similarity score between -1 and 1 (higher = more similar)
            
        Example:
            >>> sim = service.similarity(emb1, emb2)
            >>> print(f"Similarity: {sim:.2f}")
        """
        try:
            if embedding1 is None or embedding2 is None:
                return 0.0
            
            # Normalize embeddings
            emb1_norm = embedding1 / np.linalg.norm(embedding1)
            emb2_norm = embedding2 / np.linalg.norm(embedding2)
            
            # Cosine similarity
            similarity = np.dot(emb1_norm, emb2_norm)
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0
    
    def get_embedding_dimension(self):
        """
        Get the dimension of embeddings produced by this model.
        
        Returns:
            int: Embedding dimension (384 for all-MiniLM-L6-v2)
        """
        return 384