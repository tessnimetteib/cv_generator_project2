"""
CV Generation Services
=====================

This package contains all services for CV generation:
- Embedding Service: Convert text to vectors
- RAG Service: Retrieve similar examples from KB
- LLM Service Ollama: Call Llama2 locally (FREE!)
- CV Generation Service: Orchestrate everything
"""

# Import services
from .embedding_service import EmbeddingService
from .rag_service import RAGService
from .llm_service_ollama import LLMServiceOllama
from .cv_generation_service import CVGenerationService

# Public API
__all__ = [
    'EmbeddingService',
    'RAGService',
    'LLMServiceOllama',
    'CVGenerationService',
]