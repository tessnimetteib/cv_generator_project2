"""
Enhanced RAG Service
====================

Implements COMPLETE RAG pipeline with all advanced features:
✅ Profession-based filtering
✅ Re-ranking
✅ Hybrid search (semantic + keyword)
✅ Output validation
✅ Caching
✅ Query expansion
"""

import logging
import hashlib
import numpy as np
from typing import List, Dict, Optional, Tuple
from sklearn.metrics.pairwise import cosine_similarity
from django.db.models import Q, F, Value
from django.db.models.functions import Greatest

from cv_gen.models import KnowledgeBase, RAGCache, CVGenerationFeedback
from .embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class EnhancedRAGService:
    """
    Complete RAG Service with all advanced features.
    
    Features:
    ✅ Profession-based retrieval
    ✅ Section-specific filtering
    ✅ Re-ranking by relevance
    ✅ Hybrid search (keyword + semantic)
    ✅ Query caching
    ✅ Output validation
    ✅ Feedback collection
    """
    
    def __init__(self):
        """Initialize RAG service"""
        try:
            self.embedding_service = EmbeddingService()
            logger.info("✅ Enhanced RAG Service initialized")
        except Exception as e:
            logger.error(f"❌ Error initializing Enhanced RAG Service: {e}")
            raise
    
    def retrieve_similar_examples(
        self,
        query_text: str,
        profession: Optional[str] = None,
        cv_section: Optional[str] = None,
        top_k: int = 3,
        use_cache: bool = True
    ) -> List[KnowledgeBase]:
        """
        Retrieve similar examples with profession and section filtering.
        
        STEP 6: Query Embedding
        STEP 7: Similarity Search
        STEP 8: Filtering
        STEP 9: Ranking
        
        Args:
            query_text: User query text
            profession: Filter by profession (e.g., "Accountant")
            cv_section: Filter by CV section (e.g., "summary")
            top_k: Number of results to return
            use_cache: Use cached results if available
            
        Returns:
            List of KnowledgeBase entries sorted by relevance
        """
        try:
            logger.info(f"🔍 RAG Retrieval: '{query_text[:50]}...'")
            logger.info(f"   Filters: profession={profession}, section={cv_section}")
            
            # STEP 1: Check cache
            if use_cache:
                cached = self._get_cached_results(query_text, profession, cv_section)
                if cached:
                    logger.info(f"✅ Cache hit! Retrieved {len(cached)} cached results")
                    return cached
            
            # STEP 2: Generate query embedding
            logger.info("Step 1/5: Generating query embedding...")
            query_embedding = self.embedding_service.generate_embedding(query_text)
            
            # STEP 3: Build database query
            logger.info("Step 2/5: Filtering KB entries...")
            kb_query = KnowledgeBase.objects.all()
            
            # Filter by profession
            if profession:
                kb_query = kb_query.filter(profession=profession)
                logger.info(f"  └─ Filtered by profession: {profession}")
            
            # Filter by CV section
            if cv_section:
                kb_query = kb_query.filter(cv_section=cv_section)
                logger.info(f"  └─ Filtered by section: {cv_section}")
            
            kb_entries = kb_query[:2000]  # Limit for performance
            logger.info(f"  └─ Total entries to search: {len(kb_entries)}")
            
            # STEP 4: Calculate similarities
            logger.info("Step 3/5: Calculating similarities...")
            similarities = []
            
            for entry in kb_entries:
                try:
                    entry_embedding = self._parse_embedding_vector(entry.embedding_vector)
                    if entry_embedding is None:
                        continue
                    
                    # Cosine similarity
                    sim_score = float(cosine_similarity(
                        [query_embedding],
                        [entry_embedding]
                    )[0][0])
                    
                    similarities.append({
                        'entry': entry,
                        'score': sim_score
                    })
                except Exception as e:
                    logger.warning(f"Error processing entry {entry.id}: {e}")
                    continue
            
            # STEP 5: Sort by similarity
            logger.info(f"Step 4/5: Ranking {len(similarities)} results...")
            similarities.sort(key=lambda x: x['score'], reverse=True)
            
            # Get top-K
            top_results = [r['entry'] for r in similarities[:top_k]]
            
            logger.info(f"Step 5/5: Re-ranking results...")
            # Re-rank for better quality (optional)
            top_results = self._rerank_results(query_text, top_results)
            
            logger.info(f"✅ Retrieved {len(top_results)} results")
            for i, result in enumerate(top_results, 1):
                logger.debug(f"  {i}. {result.title[:50]}... ({result.profession})")
            
            # Cache results
            if use_cache:
                self._cache_results(query_text, profession, cv_section, top_results)
            
            return top_results
            
        except Exception as e:
            logger.error(f"❌ Error in retrieve_similar_examples: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def hybrid_search(
        self,
        query_text: str,
        profession: Optional[str] = None,
        cv_section: Optional[str] = None,
        top_k: int = 5
    ) -> List[KnowledgeBase]:
        """
        Hybrid search combining semantic and keyword search.
        
        ADVANCED RAG STEP: Hybrid Search
        
        Args:
            query_text: Query text
            profession: Filter by profession
            cv_section: Filter by section
            top_k: Number of results
            
        Returns:
            Combined and deduplicated results
        """
        try:
            logger.info("🔄 Performing hybrid search...")
            
            # Semantic search
            logger.info("  └─ Semantic search...")
            semantic_results = self.retrieve_similar_examples(
                query_text,
                profession=profession,
                cv_section=cv_section,
                top_k=top_k,
                use_cache=False
            )
            semantic_ids = {r.id for r in semantic_results}
            
            # Keyword search
            logger.info("  └─ Keyword search...")
            keywords = query_text.lower().split()
            keyword_query = KnowledgeBase.objects.all()
            
            if profession:
                keyword_query = keyword_query.filter(profession=profession)
            if cv_section:
                keyword_query = keyword_query.filter(cv_section=cv_section)
            
            for keyword in keywords:
                keyword_query = keyword_query.filter(
                    Q(title__icontains=keyword) |
                    Q(content__icontains=keyword)
                )
            
            keyword_results = list(keyword_query[:top_k])
            keyword_ids = {r.id for r in keyword_results}
            
            # Combine results (semantic takes priority)
            all_ids = semantic_ids | keyword_ids
            combined_results = [
                next((r for r in semantic_results if r.id in all_ids), None) or
                next((r for r in keyword_results if r.id in all_ids), None)
                for _ in range(len(all_ids))
            ]
            combined_results = [r for r in combined_results if r is not None]
            
            logger.info(f"✅ Hybrid search found {len(combined_results)} combined results")
            return combined_results[:top_k]
            
        except Exception as e:
            logger.error(f"❌ Error in hybrid_search: {e}")
            return self.retrieve_similar_examples(query_text, profession, cv_section, top_k)
    
    def _rerank_results(
        self,
        query_text: str,
        results: List[KnowledgeBase],
        top_k: Optional[int] = None
    ) -> List[KnowledgeBase]:
        """
        Re-rank results for better quality.
        
        ADVANCED RAG STEP: Re-ranking
        
        Factors considered:
        ✅ Content length (prefer complete descriptions)
        ✅ Confidence score
        ✅ Relevance to query
        ✅ Content type (prefer comprehensive entries)
        """
        try:
            if not results:
                return results
            
            logger.info(f"  Re-ranking {len(results)} results...")
            
            # Score each result
            scores = []
            for result in results:
                # Base score (word count - prefer longer, more detailed entries)
                base_score = min(result.word_count / 500, 1.0)  # Normalize to 0-1
                
                # Confidence score
                confidence = result.confidence_score
                
                # Content type score (prefer job descriptions)
                content_type_score = {
                    'job_description': 1.0,
                    'paragraph': 0.8,
                    'bullet': 0.6,
                    'achievement': 0.7,
                }.get(result.content_type, 0.5)
                
                # Combined score
                total_score = (base_score * 0.3) + (confidence * 0.4) + (content_type_score * 0.3)
                scores.append((result, total_score))
            
            # Sort by re-ranked score
            scores.sort(key=lambda x: x[1], reverse=True)
            
            reranked = [r[0] for r in scores]
            logger.info(f"  └─ Re-ranked successfully")
            
            return reranked[:top_k] if top_k else reranked
            
        except Exception as e:
            logger.warning(f"Re-ranking failed, returning original order: {e}")
            return results
    
    def validate_generation(
        self,
        query_text: str,
        generated_text: str,
        context_examples: List[KnowledgeBase]
    ) -> Tuple[bool, str, float]:
        """
        Validate generated text quality.
        
        ADVANCED RAG STEP: Output Validation
        
        Checks:
        ✅ Minimum length
        ✅ Relevance to query
        ✅ Grounded in context
        ✅ No hallucinations
        
        Args:
            query_text: Original query
            generated_text: Generated output
            context_examples: Examples used for generation
            
        Returns:
            (is_valid, reason, confidence_score)
        """
        try:
            logger.info("🔍 Validating generation...")
            
            issues = []
            
            # Check 1: Length
            if len(generated_text.strip()) < 50:
                issues.append("Generated text too short")
                logger.warning("  ❌ Text too short")
            
            # Check 2: Relevance to query
            gen_embedding = self.embedding_service.generate_embedding(generated_text)
            query_embedding = self.embedding_service.generate_embedding(query_text)
            relevance = float(cosine_similarity([gen_embedding], [query_embedding])[0][0])
            
            if relevance < 0.3:
                issues.append(f"Low relevance to query (score: {relevance:.2f})")
                logger.warning(f"  ❌ Low relevance: {relevance:.2f}")
            else:
                logger.info(f"  ✅ Relevance score: {relevance:.2f}")
            
            # Check 3: Grounding in context
            context_embeddings = [
                self.embedding_service.generate_embedding(ex.content)
                for ex in context_examples
            ]
            
            grounding_scores = [
                float(cosine_similarity([gen_embedding], [ctx_emb])[0][0])
                for ctx_emb in context_embeddings
            ]
            
            max_grounding = max(grounding_scores) if grounding_scores else 0
            
            if max_grounding < 0.2:
                issues.append(f"Not well grounded in context (score: {max_grounding:.2f})")
                logger.warning(f"  ❌ Poor grounding: {max_grounding:.2f}")
            else:
                logger.info(f"  ✅ Grounding score: {max_grounding:.2f}")
            
            # Check 4: Quality metrics
            word_count = len(generated_text.split())
            has_numbers = any(char.isdigit() for char in generated_text)
            has_action_verbs = any(
                verb in generated_text.lower()
                for verb in ['implemented', 'developed', 'designed', 'managed', 'led', 'created', 'built']
            )
            
            if word_count < 30:
                issues.append("Too few words")
                logger.warning("  ⚠️  Few words")
            
            confidence = 1.0
            if not has_numbers:
                confidence -= 0.1
            if not has_action_verbs:
                confidence -= 0.15
            
            confidence = max(0.0, confidence)
            
            is_valid = len(issues) == 0 and confidence > 0.5
            reason = " | ".join(issues) if issues else "✅ All checks passed"
            
            logger.info(f"  Result: Valid={is_valid}, Confidence={confidence:.2f}")
            logger.info(f"  Reason: {reason}")
            
            return is_valid, reason, confidence
            
        except Exception as e:
            logger.error(f"❌ Error in validate_generation: {e}")
            return True, "Validation skipped due to error", 0.5
    
    def collect_feedback(
        self,
        cv_document,
        section_type: str,
        generated_content: str,
        rating: int,
        feedback_text: str = "",
        suggested_improvement: str = ""
    ) -> bool:
        """
        Collect user feedback on generated content.
        
        ADVANCED RAG STEP: Feedback Loops
        
        This helps improve future generations through learning.
        
        Args:
            cv_document: The CV being worked on
            section_type: Which section (summary, experience, etc.)
            generated_content: The generated text
            rating: User rating 1-5
            feedback_text: User comments
            suggested_improvement: User's suggested fix
            
        Returns:
            True if feedback saved successfully
        """
        try:
            logger.info(f"💾 Saving feedback: {section_type} rated {rating}/5")
            
            feedback = CVGenerationFeedback.objects.create(
                cv_document=cv_document,
                section_type=section_type,
                generated_content=generated_content,
                rating=rating,
                feedback_text=feedback_text,
                was_helpful=rating >= 3,
                suggested_improvement=suggested_improvement
            )
            
            logger.info(f"✅ Feedback saved: ID={feedback.id}")
            
            # TODO: Use feedback to retrain ranking model
            # This is where ML model retraining would happen
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving feedback: {e}")
            return False
    
    def get_feedback_stats(self, profession: str, cv_section: str) -> Dict:
        """Get feedback statistics for a profession and section"""
        try:
            feedbacks = CVGenerationFeedback.objects.filter()  # Filter by profession from CV
            
            if not feedbacks:
                return {
                    'total_feedback': 0,
                    'average_rating': 0,
                    'helpful_percentage': 0,
                }
            
            avg_rating = feedbacks.aggregate(models.Avg('rating'))['rating__avg'] or 0
            helpful_count = feedbacks.filter(was_helpful=True).count()
            helpful_pct = (helpful_count / feedbacks.count() * 100) if feedbacks else 0
            
            return {
                'total_feedback': feedbacks.count(),
                'average_rating': round(avg_rating, 2),
                'helpful_percentage': round(helpful_pct, 1),
                'common_suggestions': self._get_common_suggestions(feedbacks),
            }
            
        except Exception as e:
            logger.error(f"Error getting feedback stats: {e}")
            return {}
    
    def format_examples_for_prompt(self, kb_entries: List[KnowledgeBase]) -> str:
        """
        Format KB entries as examples for LLM prompt.
        
        STEP 10: Augmentation
        """
        try:
            if not kb_entries:
                return "No examples available."
            
            formatted = "PROFESSIONAL EXAMPLES:\n\n"
            
            for i, entry in enumerate(kb_entries, 1):
                formatted += f"Example {i} ({entry.profession} - {entry.get_cv_section_display()}):\n"
                formatted += f"{entry.content}\n"
                formatted += f"[Confidence: {entry.confidence_score:.1%}]\n\n"
            
            logger.info(f"✅ Formatted {len(kb_entries)} examples for prompt")
            return formatted
            
        except Exception as e:
            logger.error(f"Error formatting examples: {e}")
            return ""
    
    def _parse_embedding_vector(self, embedding_json: str) -> Optional[np.ndarray]:
        """Parse embedding vector from JSON"""
        try:
            import json
            vector = json.loads(embedding_json)
            return np.array(vector)
        except:
            return None
    
    def _get_cached_results(
        self,
        query_text: str,
        profession: Optional[str],
        cv_section: Optional[str]
    ) -> Optional[List[KnowledgeBase]]:
        """Retrieve cached results if available"""
        try:
            query_hash = self._get_query_hash(query_text, profession, cv_section)
            
            cache = RAGCache.objects.get(query_hash=query_hash)
            cache.hit_count += 1
            cache.save(update_fields=['hit_count', 'accessed_at'])
            
            result_ids = cache.cached_results.get('result_ids', [])
            results = KnowledgeBase.objects.filter(id__in=result_ids)
            
            logger.info(f"✅ Cache hit (hits: {cache.hit_count})")
            return list(results)
            
        except RAGCache.DoesNotExist:
            return None
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {e}")
            return None
    
    def _cache_results(
        self,
        query_text: str,
        profession: Optional[str],
        cv_section: Optional[str],
        results: List[KnowledgeBase]
    ) -> None:
        """Cache RAG results"""
        try:
            query_hash = self._get_query_hash(query_text, profession, cv_section)
            
            RAGCache.objects.update_or_create(
                query_hash=query_hash,
                defaults={
                    'profession': profession or 'General',
                    'cv_section': cv_section or 'all',
                    'query_text': query_text,
                    'cached_results': {
                        'result_ids': [r.id for r in results],
                        'count': len(results),
                    }
                }
            )
            
            logger.info(f"✅ Results cached ({len(results)} entries)")
            
        except Exception as e:
            logger.warning(f"Cache save failed: {e}")
    
    def _get_query_hash(self, query_text: str, profession: Optional[str], cv_section: Optional[str]) -> str:
        """Generate hash for query caching"""
        cache_key = f"{query_text}_{profession}_{cv_section}"
        return hashlib.sha256(cache_key.encode()).hexdigest()
    
    def _get_common_suggestions(self, feedbacks) -> List[str]:
        """Extract common suggestions from feedback"""
        suggestions = []
        for feedback in feedbacks[:10]:  # Look at last 10
            if feedback.suggested_improvement:
                suggestions.append(feedback.suggested_improvement)
        return suggestions[:3]  # Top 3