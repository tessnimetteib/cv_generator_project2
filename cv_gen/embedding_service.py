from sentence_transformers import SentenceTransformer
import numpy as np
import json

class EmbeddingService:
    """Service for generating and managing embeddings"""
    
    def __init__(self):
        # Load the embedding model
        # This downloads ~80MB model first time - might take a minute
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def generate_embedding(self, text):
        """Generate embedding for a text"""
        try:
            embedding = self.model.encode(text)
            # Convert numpy array to list for JSON serialization
            embedding_list = embedding.tolist()
            return embedding_list
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None
    
    def calculate_similarity(self, embedding1, embedding2):
        """Calculate cosine similarity between two embeddings"""
        try:
            # Convert lists back to numpy arrays
            emb1 = np.array(embedding1)
            emb2 = np.array(embedding2)
            
            # Calculate cosine similarity
            similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
            
            return float(similarity)
        except Exception as e:
            print(f"Error calculating similarity: {e}")
            return 0.0
    
    def find_most_similar(self, query_embedding, embeddings_list, top_k=3):
        """Find top-k most similar embeddings"""
        similarities = []
        
        for idx, emb in enumerate(embeddings_list):
            sim = self.calculate_similarity(query_embedding, emb)
            similarities.append((idx, sim))
        
        # Sort by similarity descending
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Return top-k indices
        return [idx for idx, sim in similarities[:top_k]]
    
    def batch_generate_embeddings(self, texts):
        """Generate embeddings for multiple texts"""
        embeddings = []
        for text in texts:
            emb = self.generate_embedding(text)
            embeddings.append(emb)
        return embeddings