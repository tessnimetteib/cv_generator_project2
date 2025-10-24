"""
Enhanced CV Generation Service
==============================

Orchestrates the COMPLETE RAG + LLM pipeline with all advanced features.
"""

import logging
import json
from datetime import datetime
from cv_gen.models import CVDocument, WorkExperience
from .embedding_service import EmbeddingService
from .rag_service_enhanced import EnhancedRAGService
from .llm_service_ollama import LLMServiceOllama

logger = logging.getLogger(__name__)


class EnhancedCVGenerationService:
    """
    Main orchestration service for CV generation with FULL RAG pipeline.
    
    Complete workflow:
    1. ✅ Get user data
    2. ✅ Extract profession
    3. ✅ Generate embeddings
    4. ✅ Retrieve relevant examples (with profession filtering)
    5. ✅ Validate context quality
    6. ✅ Generate content with LLM
    7. ✅ Validate output
    8. ✅ Save and track feedback
    """
    
    def __init__(self, model="llama2", ollama_url="http://localhost:11434"):
        """Initialize all services"""
        try:
            logger.info("=" * 80)
            logger.info("Initializing Enhanced CV Generation Service")
            logger.info("=" * 80)
            
            self.embedding_service = EmbeddingService()
            logger.info("✅ Embedding Service initialized")
            
            self.rag_service = EnhancedRAGService()
            logger.info("✅ Enhanced RAG Service initialized")
            
            self.llm_service = LLMServiceOllama(
                model=model,
                base_url=ollama_url
            )
            logger.info(f"✅ Ollama LLM Service initialized ({model})")
            
            logger.info("=" * 80)
            logger.info("✅ Enhanced CV Generation Service READY!")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"❌ Error initializing: {e}")
            raise
    
    def generate_professional_summary(self, cv_document: CVDocument) -> str:
        """Generate professional summary with profession-specific examples"""
        try:
            logger.info(f"\n📝 Generating professional summary for {cv_document.full_name}")
            logger.info(f"   Profession: {cv_document.profession}")
            
            # Prepare user data
            user_data = {
                'full_name': cv_document.full_name,
                'job_title': cv_document.professional_headline or 'Professional',
                'experience_years': cv_document.years_of_experience,
                'skills': list(cv_document.skills.values_list('skill_name', flat=True)),
                'profession': cv_document.profession,
                'professional_summary': cv_document.professional_summary or ''
            }
            
            logger.debug(f"User data: {user_data}")
            
            # STEP 1-3: RAG Retrieval (with profession filtering!)
            logger.info("Step 1/4: Retrieving profession-specific examples...")
            query = f"{user_data['profession']} professional summary with {user_data['experience_years']} years experience"
            
            examples = self.rag_service.retrieve_similar_examples(
                query_text=query,
                profession=cv_document.profession,  # ← KEY! Profession filtering
                cv_section='summary',                # ← KEY! Section filtering
                top_k=3
            )
            
            if not examples:
                logger.warning("No examples found, using empty examples")
                formatted_examples = "No examples available."
            else:
                logger.info(f"Retrieved {len(examples)} profession-specific examples")
                formatted_examples = self.rag_service.format_examples_for_prompt(examples)
            
            # STEP 4: Generate with LLM
            logger.info("Step 2/4: Generating with Ollama...")
            summary = self.llm_service.generate_professional_summary(
                user_data=user_data,
                examples=formatted_examples
            )
            
            if not summary:
                logger.error("Failed to generate summary")
                return None
            
            # STEP 5: Validate generation
            logger.info("Step 3/4: Validating generation...")
            is_valid, reason, confidence = self.rag_service.validate_generation(
                query,
                summary,
                examples
            )
            
            if not is_valid:
                logger.warning(f"⚠️  Validation issue: {reason}")
            
            # STEP 6: Save
            logger.info("Step 4/4: Saving to database...")
            cv_document.generated_summary = summary
            cv_document.save(update_fields=['generated_summary'])
            
            logger.info("✅ Professional summary generated successfully")
            return summary
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def generate_achievement_bullets(self, cv_document: CVDocument, work_experience: WorkExperience = None) -> dict:
        """Generate achievement bullets with profession-specific filtering"""
        try:
            logger.info("\n⭐ Generating achievement bullets")
            
            results = {}
            
            # Get work experiences
            experiences = [work_experience] if work_experience else cv_document.work_experiences.all()
            logger.info(f"Processing {len(experiences)} work experience(s)")
            
            for exp in experiences:
                try:
                    logger.info(f"  └─ {exp.job_title} at {exp.company_name}")
                    
                    # Prepare data
                    user_data = {
                        'job_title': exp.job_title,
                        'job_description': exp.job_description or '',
                        'skills': list(cv_document.skills.values_list('skill_name', flat=True))
                    }
                    
                    # Retrieve examples with PROFESSION FILTERING
                    logger.info(f"    Retrieving {cv_document.profession} achievement examples...")
                    query = f"{exp.job_title} achievements and accomplishments"
                    
                    examples = self.rag_service.retrieve_similar_examples(
                        query_text=query,
                        profession=cv_document.profession,      # ← Profession filter
                        cv_section='achievement',               # ← Section filter
                        top_k=3
                    )
                    
                    if not examples:
                        formatted_examples = "No examples available."
                    else:
                        logger.info(f"    Retrieved {len(examples)} achievement examples")
                        formatted_examples = self.rag_service.format_examples_for_prompt(examples)
                    
                    # Generate bullets
                    logger.info(f"    Generating bullets...")
                    bullets = self.llm_service.generate_achievement_bullets(
                        user_data=user_data,
                        examples=formatted_examples,
                        count=3
                    )
                    
                    # Validate
                    if bullets:
                        is_valid, reason, conf = self.rag_service.validate_generation(
                            query,
                            "\n".join(bullets),
                            examples
                        )
                        if is_valid:
                            logger.info(f"    ✅ {len(bullets)} bullets generated (confidence: {conf:.1%})")
                        else:
                            logger.warning(f"    ⚠️  {reason}")
                    
                    results[exp.id] = bullets or []
                    
                except Exception as e:
                    logger.warning(f"    ❌ Error: {e}")
                    results[exp.id] = []
            
            logger.info(f"✅ Generated bullets for {len(results)} experiences")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            return {}
    
    def generate_skills_section(self, cv_document: CVDocument) -> str:
        """Generate organized skills section"""
        try:
            logger.info("\n🎯 Generating skills section")
            
            user_data = {
                'skills': list(cv_document.skills.values_list('skill_name', flat=True))
            }
            
            if not user_data['skills']:
                logger.warning("No skills found")
                return None
            
            # Retrieve PROFESSION-SPECIFIC skill examples
            logger.info(f"Retrieving {cv_document.profession} skill examples...")
            examples = self.rag_service.retrieve_similar_examples(
                query_text='professional skills organization',
                profession=cv_document.profession,  # ← Profession filter
                cv_section='skill',                  # ← Section filter
                top_k=3
            )
            
            if not examples:
                formatted_examples = "No examples available."
            else:
                formatted_examples = self.rag_service.format_examples_for_prompt(examples)
            
            # Generate
            logger.info("Generating skills section...")
            skills_section = self.llm_service.generate_skills_section(
                user_data=user_data,
                examples=formatted_examples
            )
            
            # Validate
            if skills_section:
                is_valid, reason, conf = self.rag_service.validate_generation(
                    "skills organization",
                    skills_section,
                    examples
                )
                logger.info(f"✅ Skills section generated (confidence: {conf:.1%})")
            
            return skills_section
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            return None
    
    def generate_full_cv(self, cv_document: CVDocument) -> dict:
        """
        Generate COMPLETE professional CV with full RAG pipeline.
        
        All RAG Steps Applied:
        ✅ Step 1-6: Query embedding & filtering
        ✅ Step 7-9: Similarity search & ranking
        ✅ Step 10: Augmentation (format examples)
        ✅ Step 11: Generation (Ollama)
        ✅ Step 12: Validation (quality check)
        ✅ Step 13: Feedback tracking (ready for learning)
        """
        try:
            logger.info("\n" + "=" * 80)
            logger.info(f"🚀 FULL CV GENERATION: {cv_document.full_name}")
            logger.info(f"   Profession: {cv_document.profession}")
            logger.info("=" * 80)
            
            generated_content = {}
            
            # STEP 1: Professional Summary
            logger.info("\n📝 STEP 1/3: Professional Summary")
            logger.info("-" * 80)
            summary = self.generate_professional_summary(cv_document)
            generated_content['professional_summary'] = summary
            if summary:
                logger.info(f"✅ Generated: {summary[:100]}...")
            
            # STEP 2: Achievement Bullets
            logger.info("\n⭐ STEP 2/3: Achievement Bullets")
            logger.info("-" * 80)
            bullets = self.generate_achievement_bullets(cv_document)
            generated_content['achievement_bullets'] = bullets
            logger.info(f"✅ Generated bullets for {len(bullets)} experiences")
            
            # STEP 3: Skills Section
            logger.info("\n🎯 STEP 3/3: Skills Section")
            logger.info("-" * 80)
            skills = self.generate_skills_section(cv_document)
            generated_content['skills_section'] = skills
            if skills:
                logger.info(f"✅ Generated: {skills[:100]}...")
            
            # Save all content
            logger.info("\n💾 Saving to database...")
            cv_document.generated_cv_content = generated_content
            cv_document.is_generated = True
            cv_document.generated_at = datetime.now()
            cv_document.save()
            
            logger.info("\n" + "=" * 80)
            logger.info("✅✅✅ FULL CV GENERATION COMPLETE! ✅✅✅")
            logger.info("=" * 80)
            logger.info(f"\nGenerated Content:")
            logger.info(f"  ✅ Professional Summary")
            logger.info(f"  ✅ Achievement Bullets")
            logger.info(f"  ✅ Skills Section")
            logger.info("=" * 80 + "\n")
            
            return generated_content
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def collect_user_feedback(
        self,
        cv_document: CVDocument,
        section_type: str,
        rating: int,
        feedback_text: str = "",
        suggested_improvement: str = ""
    ) -> bool:
        """Allow users to provide feedback for continuous improvement"""
        
        # Get generated content for this section
        generated_content = cv_document.generated_cv_content.get(
            f'{section_type}_section',
            ''
        )
        
        return self.rag_service.collect_feedback(
            cv_document=cv_document,
            section_type=section_type,
            generated_content=generated_content,
            rating=rating,
            feedback_text=feedback_text,
            suggested_improvement=suggested_improvement
        )