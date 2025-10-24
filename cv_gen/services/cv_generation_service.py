"""
CV Generation Service
====================

Orchestrates the entire RAG + LLM pipeline for CV generation.
Uses Ollama + Llama2 for FREE, local, private CV generation!
"""

import logging
from cv_gen.models import CVDocument
from .embedding_service import EmbeddingService
from .rag_service import RAGService
from .llm_service_ollama import LLMServiceOllama

logger = logging.getLogger(__name__)


class CVGenerationService:
    """
    Main orchestration service for CV generation.
    
    Workflow:
    1. Get user data from database
    2. Generate embeddings for user data
    3. Retrieve similar examples from KB (RAG)
    4. Generate professional content using Ollama Llama2
    5. Save generated content to database
    
    Uses Ollama for:
    ✅ 100% FREE
    ✅ 100% PRIVATE (local)
    ✅ 100% UNLIMITED
    ✅ No API keys needed
    """
    
    def __init__(self, model="llama2", ollama_url="http://localhost:11434"):
        """
        Initialize CV Generation Service with Ollama.
        
        Args:
            model (str): Ollama model (llama2, mistral, neural-chat)
            ollama_url (str): Ollama server URL
        """
        try:
            logger.info("=" * 80)
            logger.info("Initializing CV Generation Service")
            logger.info(f"Model: {model}")
            logger.info(f"Ollama URL: {ollama_url}")
            logger.info("=" * 80)
            
            # Initialize services
            self.embedding_service = EmbeddingService()
            logger.info("✅ Embedding Service initialized")
            
            self.rag_service = RAGService()
            logger.info("✅ RAG Service initialized")
            
            self.llm_service = LLMServiceOllama(
                model=model,
                base_url=ollama_url
            )
            logger.info(f"✅ Ollama LLM Service initialized with {model}")
            
            logger.info("=" * 80)
            logger.info("✅ CV Generation Service READY!")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"❌ Error initializing CV Generation Service: {e}")
            logger.error("\n⚠️  TROUBLESHOOTING:")
            logger.error("  1. Make sure Ollama is running:")
            logger.error("     ollama run llama2")
            logger.error("  2. Check Ollama is accessible at http://localhost:11434")
            logger.error("  3. Try a different model:")
            logger.error("     ollama run mistral")
            raise
    
    def generate_professional_summary(self, cv_document):
        """
        Generate professional summary for CV.
        
        Args:
            cv_document (CVDocument): User's CV document
            
        Returns:
            str: Generated professional summary
        """
        try:
            logger.info(f"Generating professional summary for CV {cv_document.id}")
            logger.info(f"User: {cv_document.full_name}")
            
            # Prepare user data
            user_data = {
                'full_name': cv_document.full_name,
                'job_title': cv_document.professional_headline or 'Professional',
                'experience_years': self._calculate_experience_years(cv_document),
                'skills': list(cv_document.skills.values_list('skill_name', flat=True)),
                'professional_summary': cv_document.professional_summary or ''
            }
            
            logger.debug(f"User Data: {user_data}")
            
            # Step 1: Retrieve similar examples using RAG
            logger.info("Step 1/3: Retrieving similar examples from KB...")
            query = f"{user_data['job_title']} professional {user_data['experience_years']} years"
            examples = self.rag_service.retrieve_similar_examples(
                query_text=query,
                category='summary',
                top_k=3
            )
            
            if not examples:
                logger.warning("No similar examples found, using empty examples")
                formatted_examples = "No examples available."
            else:
                logger.info(f"Retrieved {len(examples)} similar examples")
                formatted_examples = self.rag_service.format_examples_for_prompt(examples)
            
            # Step 2: Generate using Ollama Llama2
            logger.info("Step 2/3: Generating with Ollama Llama2...")
            summary = self.llm_service.generate_professional_summary(
                user_data=user_data,
                examples=formatted_examples
            )
            
            if summary:
                logger.info("✅ Professional summary generated")
                logger.debug(f"Generated summary: {summary[:100]}...")
                return summary
            else:
                logger.error("Failed to generate summary")
                return None
            
        except Exception as e:
            logger.error(f"❌ Error generating professional summary: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def generate_achievement_bullets(self, cv_document, work_experience=None):
        """
        Generate achievement bullets for work experience.
        
        Args:
            cv_document (CVDocument): User's CV document
            work_experience (WorkExperience, optional): Specific job to generate for
            
        Returns:
            dict: Generated bullets by work experience ID
        """
        try:
            logger.info("Generating achievement bullets")
            
            results = {}
            
            # Get work experiences to process
            if work_experience:
                experiences = [work_experience]
            else:
                experiences = cv_document.work_experiences.all()
            
            logger.info(f"Processing {len(experiences)} work experience(s)")
            
            for exp in experiences:
                try:
                    logger.info(f"Generating bullets for: {exp.job_title} at {exp.company_name}")
                    
                    # Prepare user data
                    user_data = {
                        'job_title': exp.job_title,
                        'job_description': exp.job_description or '',
                        'skills': list(cv_document.skills.values_list('skill_name', flat=True))
                    }
                    
                    # Step 1: Retrieve similar examples
                    logger.info("Step 1/2: Retrieving achievement examples...")
                    query = f"{exp.job_title} achievements accomplishments"
                    examples = self.rag_service.retrieve_similar_examples(
                        query_text=query,
                        category='achievement',
                        top_k=3
                    )
                    
                    if not examples:
                        formatted_examples = "No examples available."
                    else:
                        logger.info(f"Retrieved {len(examples)} achievement examples")
                        formatted_examples = self.rag_service.format_examples_for_prompt(examples)
                    
                    # Step 2: Generate bullets with Ollama
                    logger.info("Step 2/2: Generating achievement bullets with Ollama...")
                    bullets = self.llm_service.generate_achievement_bullets(
                        user_data=user_data,
                        examples=formatted_examples,
                        count=3
                    )
                    
                    results[exp.id] = bullets
                    logger.info(f"✅ Generated {len(bullets)} bullets for {exp.id}")
                    logger.debug(f"Bullets: {bullets}")
                    
                except Exception as e:
                    logger.warning(f"Error generating bullets for experience {exp.id}: {e}")
                    logger.debug(f"Traceback: {e}", exc_info=True)
                    results[exp.id] = []
                    continue
            
            logger.info(f"✅ Generated bullets for {len(results)} work experience(s)")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error generating achievement bullets: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {}
    
    def generate_skills_section(self, cv_document):
        """
        Generate organized skills section.
        
        Args:
            cv_document (CVDocument): User's CV document
            
        Returns:
            str: Organized skills text
        """
        try:
            logger.info("Generating skills section")
            
            # Prepare user data
            user_data = {
                'skills': list(cv_document.skills.values_list('skill_name', flat=True))
            }
            
            if not user_data['skills']:
                logger.warning("No skills found in CV")
                return None
            
            logger.info(f"Found {len(user_data['skills'])} skills to organize")
            
            # Step 1: Retrieve similar examples
            logger.info("Step 1/2: Retrieving skills examples...")
            examples = self.rag_service.retrieve_similar_examples(
                query_text='professional skills organization',
                category='skill',
                top_k=3
            )
            
            if not examples:
                formatted_examples = "No examples available."
            else:
                logger.info(f"Retrieved {len(examples)} skills examples")
                formatted_examples = self.rag_service.format_examples_for_prompt(examples)
            
            # Step 2: Generate skills section with Ollama
            logger.info("Step 2/2: Generating organized skills section with Ollama...")
            skills_section = self.llm_service.generate_skills_section(
                user_data=user_data,
                examples=formatted_examples
            )
            
            logger.info("✅ Skills section generated")
            logger.debug(f"Skills section preview: {skills_section[:100] if skills_section else 'None'}...")
            return skills_section
            
        except Exception as e:
            logger.error(f"❌ Error generating skills section: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def generate_full_cv(self, cv_document):
        """
        Generate complete professional CV.
        
        This is the MAIN method that orchestrates the entire RAG + LLM pipeline.
        
        Args:
            cv_document (CVDocument): User's CV document
            
        Returns:
            dict: Generated CV content with all sections
            
        Example:
            >>> from cv_gen.models import CVDocument
            >>> from cv_gen.services import CVGenerationService
            >>> 
            >>> cv = CVDocument.objects.get(id=1)
            >>> service = CVGenerationService()
            >>> result = service.generate_full_cv(cv)
            >>> print(result['professional_summary'])
        """
        try:
            logger.info("=" * 80)
            logger.info(f"Starting FULL CV generation for {cv_document.full_name}")
            logger.info("=" * 80)
            
            generated_content = {}
            
            # Step 1: Generate professional summary
            logger.info("\n📝 STEP 1/3: Generating professional summary...")
            logger.info("-" * 80)
            summary = self.generate_professional_summary(cv_document)
            generated_content['professional_summary'] = summary
            if summary:
                logger.info(f"✅ Summary generated: {summary[:80]}...")
            else:
                logger.warning("⚠️  Failed to generate summary")
            
            # Step 2: Generate achievement bullets
            logger.info("\n⭐ STEP 2/3: Generating achievement bullets...")
            logger.info("-" * 80)
            bullets = self.generate_achievement_bullets(cv_document)
            generated_content['achievement_bullets'] = bullets
            logger.info(f"✅ Generated bullets for {len(bullets)} work experience(s)")
            
            # Step 3: Generate skills section
            logger.info("\n🎯 STEP 3/3: Generating skills section...")
            logger.info("-" * 80)
            skills = self.generate_skills_section(cv_document)
            generated_content['skills_section'] = skills
            if skills:
                logger.info(f"✅ Skills section generated: {skills[:80]}...")
            else:
                logger.warning("⚠️  Failed to generate skills section")
            
            # Step 4: Save to database
            logger.info("\n💾 STEP 4/4: Saving to database...")
            logger.info("-" * 80)
            self._save_generated_content(cv_document, generated_content)
            logger.info("✅ Content saved to database")
            
            logger.info("\n" + "=" * 80)
            logger.info("✅✅✅ FULL CV GENERATION COMPLETE! ✅✅✅")
            logger.info("=" * 80)
            logger.info(f"\nGenerated Content:")
            logger.info(f"  - Professional Summary: {'✅' if generated_content.get('professional_summary') else '❌'}")
            logger.info(f"  - Achievement Bullets: {'✅' if generated_content.get('achievement_bullets') else '❌'}")
            logger.info(f"  - Skills Section: {'✅' if generated_content.get('skills_section') else '❌'}")
            logger.info("=" * 80 + "\n")
            
            return generated_content
            
        except Exception as e:
            logger.error(f"❌ Error generating full CV: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def _calculate_experience_years(self, cv_document):
        """
        Calculate total years of experience from work entries.
        
        Args:
            cv_document (CVDocument): User's CV document
            
        Returns:
            int: Total years of experience (rounded down)
        """
        try:
            from datetime import datetime
            
            total_years = 0
            
            for exp in cv_document.work_experiences.all():
                if exp.start_date:
                    end = exp.end_date or datetime.now().date()
                    delta = end - exp.start_date
                    years = delta.days / 365.25
                    total_years += years
            
            result = max(int(total_years), 0)
            logger.debug(f"Total experience calculated: {result} years")
            return result
            
        except Exception as e:
            logger.warning(f"Error calculating experience years: {e}")
            return 0
    
    def _save_generated_content(self, cv_document, generated_content):
        """
        Save generated content to database.
        
        Args:
            cv_document (CVDocument): User's CV document
            generated_content (dict): Generated content dictionary
            
        Raises:
            Exception: If save fails
        """
        try:
            logger.info("Saving generated content to database")
            
            # Save professional summary
            if generated_content.get('professional_summary'):
                cv_document.generated_summary = generated_content['professional_summary']
                logger.debug("Saved generated_summary")
            
            # Mark as generated
            cv_document.is_generated = True
            cv_document.generated_at = __import__('django.utils.timezone', fromlist=['now']).now()
            
            # Save all content as JSON
            import json
            cv_document.generated_cv_content = json.dumps(generated_content, indent=2)
            
            # Save to database
            cv_document.save()
            logger.info(f"✅ Content saved to database for CV {cv_document.id}")
            
        except Exception as e:
            logger.error(f"❌ Error saving generated content: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise