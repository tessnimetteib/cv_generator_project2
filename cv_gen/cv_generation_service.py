from .llm_service import LLMService
from .rag_service import RAGService
from .embedding_service import EmbeddingService
from cv_gen.models import CVDocument, WorkExperience, Education, Skill
from datetime import datetime

class CVGenerationService:
    """Service for generating complete CVs"""
    
    def __init__(self):
        self.llm_service = LLMService()
        self.rag_service = RAGService()
        self.embedding_service = EmbeddingService()
    
    def generate_complete_cv(self, cv_document_id):
        """Generate a complete CV"""
        
        # Retrieve CV document
        cv_doc = CVDocument.objects.get(id=cv_document_id)
        
        # Get all related data
        work_experiences = WorkExperience.objects.filter(cv_document=cv_doc)
        educations = Education.objects.filter(cv_document=cv_doc)
        skills = Skill.objects.filter(cv_document=cv_doc)
        
        # Step 1: Generate professional summary
        summary = self._generate_summary(cv_doc)
        cv_doc.generated_summary = summary
        
        # Step 2: Generate work experience bullets
        experience_section = self._generate_experience(work_experiences)
        
        # Step 3: Format education section
        education_section = self._format_education(educations)
        
        # Step 4: Organize skills
        skills_section = self._organize_skills(skills)
        
        # Step 5: Combine all sections into complete CV
        complete_cv = self._format_complete_cv(
            cv_doc,
            summary,
            experience_section,
            education_section,
            skills_section
        )
        
        # Save to database
        cv_doc.generated_cv_content = complete_cv
        cv_doc.is_generated = True
        cv_doc.save()
        
        return complete_cv
    
    def _generate_summary(self, cv_doc):
        """Generate professional summary using RAG"""
        
        # Create query for RAG
        query = f"professional summary for {cv_doc.professional_headline}"
        
        # Retrieve relevant examples
        examples = self.rag_service.retrieve_similar_examples(
            query,
            category='summary',
            count=3
        )
        
        # Format examples for prompt
        examples_text = self.rag_service.format_examples_for_prompt(examples)
        
        # Generate summary with LLM
        summary = self.llm_service.generate_professional_summary(
            headline=cv_doc.professional_headline,
            years_experience="5",  # Default - can be extracted
            expertise=cv_doc.professional_headline,
            examples=examples_text
        )
        
        return summary
    
    def _generate_experience(self, work_experiences):
        """Generate work experience bullets using RAG"""
        
        experience_section = []
        
        for job in work_experiences:
            # Create query for RAG
            query = f"achievement bullets for {job.job_title}"
            
            # Determine role type from job title
            role_type = self._infer_role_type(job.job_title)
            
            # Retrieve relevant examples
            examples = self.rag_service.retrieve_similar_examples(
                query,
                category='achievement',
                role_type=role_type,
                count=3
            )
            
            # Format examples
            examples_text = self.rag_service.format_examples_for_prompt(examples)
            
            # Generate bullets
            bullets = self.llm_service.generate_work_bullets(
                job_title=job.job_title,
                company=job.company_name,
                job_description=job.job_description,
                achievements=job.achievements,
                technologies=job.technologies,
                examples=examples_text
            )
            
            # Save generated bullets
            job.generated_bullets = bullets
            job.save()
            
            # Format for CV
            end_date = "Present" if job.is_current else job.end_date.strftime('%B %Y')
            
            job_entry = {
                'title': job.job_title,
                'company': job.company_name,
                'location': job.location if job.location else '',
                'dates': f"{job.start_date.strftime('%B %Y')} - {end_date}",
                'bullets': bullets
            }
            
            experience_section.append(job_entry)
        
        return experience_section
    
    def _format_education(self, educations):
        """Format education section"""
        
        education_section = []
        
        for edu in educations:
            formatted_edu = {
                'degree': edu.degree,
                'field': edu.field_of_study,
                'institution': edu.institution,
                'graduation': edu.graduation_date.strftime('%B %Y'),
                'gpa': str(edu.gpa) if edu.gpa else None,
                'honors': edu.honors if edu.honors else None,
                'coursework': edu.relevant_coursework if edu.relevant_coursework else None
            }
            
            education_section.append(formatted_edu)
        
        return education_section
    
    def _organize_skills(self, skills):
        """Organize skills by category"""
        
        skills_dict = {
            'Technical': [],
            'Soft': [],
            'Language': [],
            'Certification': []
        }
        
        for skill in skills:
            skills_dict[skill.category].append(skill.skill_name)
        
        # Remove empty categories
        skills_dict = {k: v for k, v in skills_dict.items() if v}
        
        return skills_dict
    
    def _format_complete_cv(self, cv_doc, summary, experience_section, education_section, skills_section):
        """Format all sections into complete CV text"""
        
        cv_text = f"""
════════════════════════════════════════════════════════
                 {cv_doc.full_name.upper()}
════════════════════════════════════════════════════════

{cv_doc.professional_headline}

Email: {cv_doc.email} | Phone: {cv_doc.phone}
Location: {cv_doc.location}

════════════════════════════════════════════════════════
PROFESSIONAL SUMMARY
════════════════════════════════════════════════════════
{summary}

════════════════════════════════════════════════════════
WORK EXPERIENCE
════════════════════════════════════════════════════════
"""
        
        for job in experience_section:
            cv_text += f"""
{job['title']} | {job['company']}
{job['location']} | {job['dates']}
{job['bullets']}

"""
        
        cv_text += """
════════════════════════════════════════════════════════
EDUCATION
════════════════════════════════════════════════════════
"""
        
        for edu in education_section:
            cv_text += f"""
{edu['degree']} in {edu['field']}
{edu['institution']} | {edu['graduation']}
"""
            if edu['gpa']:
                cv_text += f"   GPA: {edu['gpa']}\n"
            if edu['honors']:
                cv_text += f"   {edu['honors']}\n"
        
        cv_text += """
════════════════════════════════════════════════════════
SKILLS
════════════════════════════════════════════════════════
"""
        
        for category, skill_list in skills_section.items():
            cv_text += f"\n   {category.upper()}\n"
            cv_text += "   " + ", ".join(skill_list) + "\n"
        
        return cv_text
    
    def _infer_role_type(self, job_title):
        """Infer role type from job title"""
        
        job_title_lower = job_title.lower()
        
        if any(word in job_title_lower for word in ['backend', 'api', 'server', 'python', 'java', 'golang']):
            return 'backend_developer'
        elif any(word in job_title_lower for word in ['frontend', 'react', 'angular', 'vue', 'ui']):
            return 'frontend_developer'
        elif any(word in job_title_lower for word in ['manager', 'director', 'lead', 'head']):
            return 'manager'
        elif any(word in job_title_lower for word in ['designer', 'ux', 'ui']):
            return 'designer'
        else:
            return 'general'