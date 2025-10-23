import os
from openai import OpenAI
from django.conf import settings

class LLMService:
    """Service for interacting with OpenAI LLM"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-3.5-turbo"
    
    def generate_professional_summary(self, headline, years_experience, expertise, examples=""):
        """Generate a professional summary"""
        
        prompt = f"""You are a professional CV writer. Create a compelling professional summary.

Candidate Information:
- Professional Headline: {headline}
- Years of Experience: {years_experience}
- Main Expertise: {expertise}

Reference Examples (use as style guide only):
{examples}

Requirements:
- 2-3 sentences maximum
- Start with a strong descriptor (Results-driven, Strategic, Innovative, etc.)
- Include years of experience and key expertise
- Highlight impact and achievements
- Professional and impactful tone

Generate ONLY the professional summary, no explanations or labels."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=200
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            print(f"Error generating summary: {e}")
            return f"Senior professional with {years_experience} years of {expertise} experience"
    
    def generate_work_bullets(self, job_title, company, job_description, achievements, technologies, examples=""):
        """Generate achievement bullets for work experience"""
        
        prompt = f"""You are an expert CV writer. Transform job experience into impactful achievement bullets.

Job Information:
- Title: {job_title}
- Company: {company}
- Description: {job_description}
- Achievements: {achievements}
- Technologies: {technologies}

Reference Examples (use for style only):
{examples}

Requirements for each bullet:
1. Start with strong action verb (Architected, Designed, Led, Optimized, Implemented, etc.)
2. Include specific metric or impact (%, numbers, scale, etc.)
3. Show business value or results
4. Keep to one line each
5. 3-4 bullets total

Format:
• [Bullet 1]
• [Bullet 2]
• [Bullet 3]
• [Bullet 4]

Generate ONLY the bullets with • prefix, no other text."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=300
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            print(f"Error generating work bullets: {e}")
            return f"""• {job_description}
• Utilized {technologies} to deliver results
• Contributed to {company} success"""
    
    def generate_education_section(self, institution, degree, field, gpa=None, honors=None):
        """Format education section professionally"""
        
        section = f"{degree} in {field}\n{institution}"
        
        if gpa:
            section += f" | GPA: {gpa}"
        
        if honors:
            section += f" | {honors}"
        
        return section
    
    def organize_skills(self, technical_skills, soft_skills, languages="", certifications=""):
        """Organize skills by category"""
        
        prompt = f"""Organize these skills into professional categories.

Technical Skills: {', '.join(technical_skills)}
Soft Skills: {', '.join(soft_skills)}
Languages: {languages}
Certifications: {certifications}

Format as:
TECHNICAL SKILLS
[list items with appropriate grouping]

SOFT SKILLS
[list items]

[Include Languages and Certifications sections if provided]

Return ONLY the formatted skills section, no additional text."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=300
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            print(f"Error organizing skills: {e}")
            # Fallback formatting
            skills_text = "TECHNICAL SKILLS\n"
            skills_text += ", ".join(technical_skills) + "\n\n"
            skills_text += "SOFT SKILLS\n"
            skills_text += ", ".join(soft_skills)
            return skills_text
    
    def validate_json_output(self, response_text):
        """Validate LLM output is valid"""
        import json
        try:
            json.loads(response_text)
            return True
        except:
            return False