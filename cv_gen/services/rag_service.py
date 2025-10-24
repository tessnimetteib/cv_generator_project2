"""
RAG (Retrieval-Augmented Generation) Service
=============================================

Retrieves relevant examples from Knowledge Base using semantic similarity.
"""

import numpy as np
import logging
from cv_gen.models import KnowledgeBase
from .embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class RAGService:
    """
    Service for retrieving relevant examples from Knowledge Base.
    
    Uses embedding similarity to find most relevant examples:
    1. Generate embedding from query
    2. Compare with all KB embeddings
    3. Return top N most similar entries
    """
    
    def __init__(self):
        """Initialize RAG service with embedding service"""
        try:
            logger.info("Initializing RAG Service")
            self.embedding_service = EmbeddingService()
            logger.info("✅ RAG Service initialized")
        except Exception as e:
            logger.error(f"❌ Error initializing RAG Service: {e}")
            raise
    
    def _parse_embedding_vector(self, embedding_str):
        """
        Parse embedding vector from string format in database.
        
        Args:
            embedding_str (str): Comma-separated embedding values
            
        Returns:
            np.ndarray: Embedding vector
        """
        try:
            if not embedding_str:
                return None
            
            values = [float(x.strip()) for x in embedding_str.split(',')]
            return np.array(values)
        except Exception as e:
            logger.error(f"Error parsing embedding: {e}")
            return None
    
    def retrieve_similar_examples(self, query_text, category=None, role_type=None, 
                                   industry=None, top_k=3):
        """
        Retrieve similar examples from Knowledge Base.
        
        Args:
            query_text (str): Query text to find similar examples for
            category (str, optional): Filter by category 
                (summary/achievement/skill/best_practice)
            role_type (str, optional): Filter by role type 
                (manager/designer/backend_developer/general)
            industry (str, optional): Filter by industry 
                (it/finance/hr/etc)
            top_k (int): Number of top results to return (default: 3)
            
        Returns:
            list: List of top K similar KnowledgeBase entries
            
        Example:
            >>> rag = RAGService()
            >>> examples = rag.retrieve_similar_examples(
            ...     query_text="Backend developer with 5 years",
            ...     category="achievement",
            ...     top_k=3
            ... )
            >>> for ex in examples:
            ...     print(ex.content)
        """
        try:
            logger.info(f"Retrieving similar examples for: {query_text[:50]}...")
            
            # Step 1: Generate embedding for query
            query_embedding = self.embedding_service.generate_embedding(query_text)
            if query_embedding is None:
                logger.error("Failed to generate query embedding")
                return []
            
            logger.debug(f"Query embedding generated: {query_embedding.shape}")
            
            # Step 2: Get KB entries with optional filters
            kb_query = KnowledgeBase.objects.all()
            
            if category:
                kb_query = kb_query.filter(category=category)
                logger.debug(f"Filtered by category: {category}")
            
            if role_type:
                kb_query = kb_query.filter(role_type=role_type)
                logger.debug(f"Filtered by role_type: {role_type}")
            
            if industry:
                kb_query = kb_query.filter(industry=industry)
                logger.debug(f"Filtered by industry: {industry}")
            
            kb_entries = kb_query[:1000]  # Limit to first 1000 for performance
            logger.info(f"Loaded {len(kb_entries)} KB entries for comparison")
            
            # Step 3: Calculate similarity with each entry
            similarities = []
            
            for entry in kb_entries:
                try:
                    # Parse embedding from database
                    entry_embedding = self._parse_embedding_vector(entry.embedding_vector)
                    
                    if entry_embedding is None:
                        continue
                    
                    # Calculate similarity
                    sim_score = self.embedding_service.similarity(
                        query_embedding, 
                        entry_embedding
                    )
                    
                    similarities.append({
                        'entry': entry,
                        'score': sim_score
                    })
                    
                except Exception as e:
                    logger.warning(f"Error processing KB entry {entry.id}: {e}")
                    continue
            
            logger.debug(f"Calculated similarities for {len(similarities)} entries")
            
            # Step 4: Sort by similarity (highest first)
            similarities.sort(key=lambda x: x['score'], reverse=True)
            
            # Step 5: Get top K
            top_results = similarities[:top_k]
            
            logger.info(f"Retrieved top {len(top_results)} similar examples")
            for i, result in enumerate(top_results, 1):
                logger.debug(f"  {i}. Score: {result['score']:.3f} - {result['entry'].title}")
            
            return [result['entry'] for result in top_results]
            
        except Exception as e:
            logger.error(f"Error retrieving similar examples: {e}")
            return []
    
    def retrieve_by_category(self, category, role_type=None, limit=5):
        """
        Retrieve examples by specific category.
        
        Args:
            category (str): Category to retrieve 
                (summary/achievement/skill/best_practice)
            role_type (str, optional): Filter by role type
            limit (int): Maximum number to return
            
        Returns:
            list: List of KB entries
        """
        try:
            logger.info(f"Retrieving {category} examples (limit: {limit})")
            
            query = KnowledgeBase.objects.filter(category=category)
            
            if role_type:
                query = query.filter(role_type=role_type)
            
            results = list(query[:limit])
            
            logger.info(f"Retrieved {len(results)} {category} examples")
            return results
            
        except Exception as e:
            logger.error(f"Error retrieving by category: {e}")
            return []
    
    def retrieve_by_industry(self, industry, category=None, limit=10):
        """
        Retrieve examples by industry.
        
        Args:
            industry (str): Industry to retrieve
            category (str, optional): Filter by category
            limit (int): Maximum number to return
            
        Returns:
            list: List of KB entries
        """
        try:
            logger.info(f"Retrieving {industry} examples (limit: {limit})")
            
            query = KnowledgeBase.objects.filter(industry=industry)
            
            if category:
                query = query.filter(category=category)
            
            results = list(query[:limit])
            
            logger.info(f"Retrieved {len(results)} {industry} examples")
            return results
            
        except Exception as e:
            logger.error(f"Error retrieving by industry: {e}")
            return []
    
    def format_examples_for_prompt(self, kb_entries):
        """
        Format KB entries into readable text for LLM prompt.
        
        Args:
            kb_entries (list): List of KnowledgeBase entries
            
        Returns:
            str: Formatted text with examples
            
        Example:
            >>> examples = rag.retrieve_similar_examples("Backend dev")
            >>> formatted = rag.format_examples_for_prompt(examples)
            >>> print(formatted)
            "
            PROFESSIONAL EXAMPLES:
            
            Example 1:
            Architected microservices handling 10M+ transactions...
            
            Example 2:
            Optimized database queries achieving 3x performance...
            "
        """
        try:
            if not kb_entries:
                return "No examples available."
            
            formatted = "PROFESSIONAL EXAMPLES:\n\n"
            
            for i, entry in enumerate(kb_entries, 1):
                formatted += f"Example {i}:\n"
                formatted += f"{entry.content}\n"
                formatted += f"(Category: {entry.category}, Role: {entry.role_type})\n\n"
            
            return formatted
            
        except Exception as e:
            logger.error(f"Error formatting examples: {e}")
            return ""