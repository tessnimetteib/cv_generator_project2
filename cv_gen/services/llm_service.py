"""
LLM Service
===========

Calls OpenAI API using LangChain to generate professional CV content.
"""

import os
import logging
from langchain_openai import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

logger = logging.getLogger(__name__)


class LLMService:
    """
    Service for calling OpenAI API using LangChain.
    
    Features:
    - Generates professional CV content
    - Uses LangChain for clean interface
    - Manages prompt templates
    - Handles API errors gracefully
    """
    
    def __init__(self, api_key=None, model="gpt-3.5-turbo", temperature=0.7):
        """
        Initialize LLM service.
        
        Args:
            api_key (str, optional): OpenAI API key (uses OPENAI_API_KEY env var if not provided)
            model (str): Model to use (default: gpt-3.5-turbo)
            temperature (float): Creativity level 0-1 (default: 0.7)
        """
        try:
            # Get API key from parameter or environment
            if api_key is None:
                api_key = os.getenv('OPENAI_API_KEY')
            
            if not api_key:
                raise ValueError(
                    "OpenAI API key not provided. "
                    "Set OPENAI_API_KEY environment variable or pass as parameter."
                )
            
            logger.info(f"Initializing LLM Service with model: {model}")
            
            # Initialize LangChain OpenAI (NEW IMPORT PATH)
            self.llm = OpenAI(
                api_key=api_key,
                model_name=model,
                temperature=temperature,
                max_tokens=500
            )
            
            self.model = model
            self.temperature = temperature
            
            logger.info("✅ LLM Service initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Error initializing LLM Service: {e}")
            raise
    
    def generate_professional_summary(self, user_data, examples):
        """
        Generate professional summary using LLM.
        
        Args:
            user_data (dict): User's CV data
                {
                    'full_name': str,
                    'job_title': str,
                    'experience_years': int,
                    'skills': list,
                    'professional_summary': str (optional)
                }
            examples (str): Formatted examples from RAG
            
        Returns:
            str: Generated professional summary
        """
        try:
            logger.info("Generating professional summary")
            
            # Create prompt template
            template = """You are an expert CV writer. Generate a professional 2-3 sentence summary for a job applicant.

Here are examples of professional summaries:

{examples}

Now write a professional summary for:
- Name: {full_name}
- Job Title: {job_title}
- Years of Experience: {experience_years}
- Skills: {skills}
- Background: {background}

Generate a professional summary in the same style as the examples above. Focus on achievements and expertise."""
            
            prompt = PromptTemplate(
                template=template,
                input_variables=[
                    'examples',
                    'full_name',
                    'job_title',
                    'experience_years',
                    'skills',
                    'background'
                ]
            )
            
            # Create chain
            chain = LLMChain(llm=self.llm, prompt=prompt)
            
            # Generate
            result = chain.run(
                examples=examples,
                full_name=user_data.get('full_name', 'Candidate'),
                job_title=user_data.get('job_title', 'Professional'),
                experience_years=user_data.get('experience_years', 0),
                skills=', '.join(user_data.get('skills', [])),
                background=user_data.get('professional_summary', 'Not provided')
            )
            
            logger.info("✅ Professional summary generated")
            return result.strip()
            
        except Exception as e:
            logger.error(f"❌ Error generating professional summary: {e}")
            return None
    
    def generate_achievement_bullets(self, user_data, examples, count=3):
        """
        Generate achievement bullet points.
        
        Args:
            user_data (dict): User's CV data with job description
            examples (str): Formatted examples from RAG
            count (int): Number of bullets to generate
            
        Returns:
            list: Generated achievement bullets
        """
        try:
            logger.info(f"Generating {count} achievement bullets")
            
            template = """You are an expert CV writer. Generate {count} impressive achievement bullet points.

Here are examples of professional achievement bullets:

{examples}

Now generate {count} achievement bullets for:
- Job Title: {job_title}
- Job Description: {job_description}
- Skills: {skills}

Generate bullet points in the same professional style as the examples. Start each with an action verb. Make them specific and quantifiable when possible."""
            
            prompt = PromptTemplate(
                template=template,
                input_variables=[
                    'count',
                    'examples',
                    'job_title',
                    'job_description',
                    'skills'
                ]
            )
            
            chain = LLMChain(llm=self.llm, prompt=prompt)
            
            result = chain.run(
                count=count,
                examples=examples,
                job_title=user_data.get('job_title', 'Position'),
                job_description=user_data.get('job_description', 'Not provided'),
                skills=', '.join(user_data.get('skills', []))
            )
            
            # Parse bullets
            bullets = [line.strip() for line in result.strip().split('\n') 
                      if line.strip() and (line.strip().startswith('-') or line.strip().startswith('•'))]
            
            # Clean bullets
            bullets = [b.lstrip('-•').strip() for b in bullets]
            
            logger.info(f"✅ Generated {len(bullets)} achievement bullets")
            return bullets
            
        except Exception as e:
            logger.error(f"❌ Error generating achievement bullets: {e}")
            return []
    
    def generate_skills_section(self, user_data, examples):
        """
        Generate organized skills section.
        
        Args:
            user_data (dict): User's CV data with skills
            examples (str): Formatted examples from RAG
            
        Returns:
            dict: Organized skills by category
        """
        try:
            logger.info("Generating skills section")
            
            template = """You are an expert CV writer. Organize and enhance a skills list.

Here are examples of well-organized professional skills:

{examples}

Now organize these skills into categories:
Skills provided: {skills}

Organize them into categories (Technical, Soft Skills, Tools, Languages, etc.) in the same format as the examples. Be professional and concise."""
            
            prompt = PromptTemplate(
                template=template,
                input_variables=['examples', 'skills']
            )
            
            chain = LLMChain(llm=self.llm, prompt=prompt)
            
            result = chain.run(
                examples=examples,
                skills=', '.join(user_data.get('skills', []))
            )
            
            logger.info("✅ Skills section generated")
            return result.strip()
            
        except Exception as e:
            logger.error(f"❌ Error generating skills section: {e}")
            return None
    
    def generate_job_description(self, user_data, examples):
        """
        Generate professional job description.
        
        Args:
            user_data (dict): Job details
            examples (str): Formatted examples from RAG
            
        Returns:
            str: Generated job description
        """
        try:
            logger.info("Generating job description")
            
            template = """You are an expert CV writer. Write a professional job description.

Here are examples of professional job descriptions:

{examples}

Now write a job description for:
- Job Title: {job_title}
- Company: {company}
- Duration: {start_date} to {end_date}
- Brief Description: {description}

Write in the same professional style as the examples. Be concise and impactful."""
            
            prompt = PromptTemplate(
                template=template,
                input_variables=[
                    'examples',
                    'job_title',
                    'company',
                    'start_date',
                    'end_date',
                    'description'
                ]
            )
            
            chain = LLMChain(llm=self.llm, prompt=prompt)
            
            result = chain.run(
                examples=examples,
                job_title=user_data.get('job_title', 'Position'),
                company=user_data.get('company', 'Company'),
                start_date=user_data.get('start_date', 'Date'),
                end_date=user_data.get('end_date', 'Date'),
                description=user_data.get('description', 'Not provided')
            )
            
            logger.info("✅ Job description generated")
            return result.strip()
            
        except Exception as e:
            logger.error(f"❌ Error generating job description: {e}")
            return None
    
    def generate_education_section(self, user_data, examples):
        """
        Generate professional education section.
        
        Args:
            user_data (dict): Education details
            examples (str): Formatted examples from RAG
            
        Returns:
            str: Generated education section
        """
        try:
            logger.info("Generating education section")
            
            template = """You are an expert CV writer. Write professional education section details.

Here are examples of professional education sections:

{examples}

Now write education details for:
- Institution: {institution}
- Degree: {degree}
- Field: {field}
- Graduation Date: {graduation_date}
- GPA: {gpa}
- Honors: {honors}

Write in the same professional style as the examples. Include relevant honors or achievements."""
            
            prompt = PromptTemplate(
                template=template,
                input_variables=[
                    'examples',
                    'institution',
                    'degree',
                    'field',
                    'graduation_date',
                    'gpa',
                    'honors'
                ]
            )
            
            chain = LLMChain(llm=self.llm, prompt=prompt)
            
            result = chain.run(
                examples=examples,
                institution=user_data.get('institution', 'University'),
                degree=user_data.get('degree', 'Bachelor'),
                field=user_data.get('field', 'Field'),
                graduation_date=user_data.get('graduation_date', 'Date'),
                gpa=user_data.get('gpa', 'N/A'),
                honors=user_data.get('honors', 'N/A')
            )
            
            logger.info("✅ Education section generated")
            return result.strip()
            
        except Exception as e:
            logger.error(f"❌ Error generating education section: {e}")
            return None