from django.db import models
from cv_gen.models import KnowledgeBase
from .embedding_service import EmbeddingService
import json

class RAGService:
    """Service for Retrieval-Augmented Generation"""
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.knowledge_base = KnowledgeBase.objects.all()
    
    def load_knowledge_base(self):
        """Load knowledge base entries from database"""
        return KnowledgeBase.objects.all()
    
    def add_to_knowledge_base(self, title, content, category, role_type='general', industry='general'):
        """Add new entry to knowledge base"""
        
        # Generate embedding for content
        embedding = self.embedding_service.generate_embedding(content)
        
        # Create knowledge base entry
        kb_entry = KnowledgeBase.objects.create(
            title=title,
            content=content,
            category=category,
            role_type=role_type,
            industry=industry,
            embedding_vector=json.dumps(embedding) if embedding else ""
        )
        
        return kb_entry
    
    def retrieve_similar_examples(self, query, category=None, role_type=None, count=3):
        """Retrieve similar examples from knowledge base"""
        
        # Generate embedding for query
        query_embedding = self.embedding_service.generate_embedding(query)
        
        if query_embedding is None:
            return []
        
        # Get all relevant knowledge base entries
        kb_entries = KnowledgeBase.objects.all()
        
        if category:
            kb_entries = kb_entries.filter(category=category)
        
        if role_type:
            kb_entries = kb_entries.filter(role_type=role_type)
        
        # Calculate similarities
        similarities = []
        for kb_entry in kb_entries:
            if kb_entry.embedding_vector:
                try:
                    emb = json.loads(kb_entry.embedding_vector)
                    sim = self.embedding_service.calculate_similarity(query_embedding, emb)
                    similarities.append((kb_entry, sim))
                except:
                    pass
        
        # Sort by similarity and get top-k
        similarities.sort(key=lambda x: x[1], reverse=True)
        results = [entry for entry, sim in similarities[:count]]
        
        return results
    
    def format_examples_for_prompt(self, examples):
        """Format retrieved examples for LLM prompt"""
        formatted = "REFERENCE EXAMPLES:\n"
        for idx, example in enumerate(examples, 1):
            formatted += f"\n{idx}. {example.content}\n"
        return formatted
    
    def populate_initial_knowledge_base(self):
        """Populate knowledge base with initial examples"""
        
        # Check if already populated
        if KnowledgeBase.objects.count() > 0:
            return
        
        # Achievement examples
        achievements = [
            {
                "title": "Backend API Achievement",
                "content": "Architected and deployed microservices handling 10M+ daily transactions using Django REST Framework, achieving 99.9% uptime",
                "category": "achievement",
                "role_type": "backend_developer",
                "industry": "technology"
            },
            {
                "title": "Performance Optimization",
                "content": "Optimized database queries and API response times, achieving 3x performance improvement and reducing infrastructure costs by $200K annually",
                "category": "achievement",
                "role_type": "backend_developer",
                "industry": "technology"
            },
            {
                "title": "Docker Implementation",
                "content": "Led containerization initiative using Docker, reducing deployment time by 60% and improving development velocity",
                "category": "achievement",
                "role_type": "backend_developer",
                "industry": "technology"
            },
            {
                "title": "Team Leadership",
                "content": "Mentored team of 3 junior developers, implementing code review process that reduced bugs by 40%",
                "category": "achievement",
                "role_type": "manager",
                "industry": "general"
            },
            {
                "title": "Frontend Development",
                "content": "Built responsive React component library with 50+ reusable components, improving development speed by 30%",
                "category": "achievement",
                "role_type": "frontend_developer",
                "industry": "technology"
            },
        ]
        
        # Summary examples
        summaries = [
            {
                "title": "Senior Backend Summary",
                "content": "Results-driven Senior Backend Engineer with 6+ years of proven expertise architecting scalable microservices and leading technical initiatives. Specialized in Python, Django, and cloud technologies with track record of delivering high-performance solutions.",
                "category": "summary",
                "role_type": "backend_developer",
                "industry": "technology"
            },
            {
                "title": "Manager Summary",
                "content": "Strategic Engineering Manager with 8+ years of experience leading cross-functional teams in fast-paced environments. Proven expertise in building high-performing teams, delivering products on schedule, and driving technical excellence.",
                "category": "summary",
                "role_type": "manager",
                "industry": "general"
            },
            {
                "title": "Frontend Developer Summary",
                "content": "Creative Frontend Developer with 5+ years of experience building beautiful, responsive web applications using React and modern JavaScript. Passionate about user experience and clean code architecture.",
                "category": "summary",
                "role_type": "frontend_developer",
                "industry": "technology"
            },
        ]
        
        # Best practices
        practices = [
            {
                "title": "Action Verb Best Practice",
                "content": "Always start achievement bullets with strong action verbs like: Architected, Designed, Implemented, Optimized, Led, Developed, Built, Managed, Coordinated, Orchestrated, Spearheaded, Transformed",
                "category": "best_practice",
                "role_type": "general",
                "industry": "general"
            },
            {
                "title": "Quantification Best Practice",
                "content": "Include specific metrics in achievements: percentages (40% improvement), numbers (10M+ users), time savings (60% reduction), cost savings ($200K), team size (team of 5)",
                "category": "best_practice",
                "role_type": "general",
                "industry": "general"
            },
            {
                "title": "Impact Best Practice",
                "content": "Frame achievements to show business impact: How did it help the company? How did it affect users? What was the measurable result?",
                "category": "best_practice",
                "role_type": "general",
                "industry": "general"
            },
        ]
        
        # Add all to database
        all_entries = achievements + summaries + practices
        
        for entry in all_entries:
            self.add_to_knowledge_base(
                title=entry["title"],
                content=entry["content"],
                category=entry["category"],
                role_type=entry["role_type"],
                industry=entry["industry"]
            )
        
        print(f"Loaded {len(all_entries)} knowledge base entries")