# -*- coding: utf-8 -*-
import os
import pdfplumber
import pandas as pd
from sentence_transformers import SentenceTransformer
from cv_gen.models import KnowledgeBase
import re
from tqdm import tqdm
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cv_analyzer.settings')
django.setup()

# Configuration
PDF_BASE_PATH = r"C:\Users\DELL\Desktop\resume_dataset\data\data"
CSV_PATH = r"C:\Users\DELL\Desktop\resume_dataset\Resume\Resume.csv"

class ResumeParser:
    """Parse resume text and extract sections"""
    
    def __init__(self, text, category):
        self.text = text
        self.category = category
        self.sections = self._parse_sections()
    
    def _parse_sections(self):
        """Extract main sections from resume"""
        sections = {
            'summary': '',
            'experience': '',
            'education': '',
            'skills': '',
            'accomplishments': ''
        }
        
        # Extract Summary
        summary_match = re.search(r'Summary\s*(.*?)(?=Experience|Education|Skills|Highlights|$)', 
                                 self.text, re.DOTALL | re.IGNORECASE)
        if summary_match:
            sections['summary'] = summary_match.group(1).strip()
        
        # Extract Experience
        exp_match = re.search(r'Experience\s*(.*?)(?=Education|Skills|$)', 
                             self.text, re.DOTALL | re.IGNORECASE)
        if exp_match:
            sections['experience'] = exp_match.group(1).strip()
        
        # Extract Education
        edu_match = re.search(r'Education\s*(.*?)(?=Skills|$)', 
                             self.text, re.DOTALL | re.IGNORECASE)
        if edu_match:
            sections['education'] = edu_match.group(1).strip()
        
        # Extract Skills
        skills_match = re.search(r'Skills\s*(.*?)(?=$)', 
                                self.text, re.DOTALL | re.IGNORECASE)
        if skills_match:
            sections['skills'] = skills_match.group(1).strip()
        
        # Extract Accomplishments/Highlights
        acc_match = re.search(r'(?:Accomplishments|Highlights)\s*(.*?)(?=Experience|$)', 
                             self.text, re.DOTALL | re.IGNORECASE)
        if acc_match:
            sections['accomplishments'] = acc_match.group(1).strip()
        
        return sections
    
    def extract_summary(self):
        """Extract professional summary"""
        summary = self.sections['summary']
        if summary:
            lines = [line.strip() for line in summary.split('\n') if line.strip()]
            if lines:
                text = lines[0]
                return text[:300] if len(text) > 300 else text
        return None
    
    def extract_achievements(self):
        """Extract achievement bullet points"""
        achievements = []
        
        # From accomplishments section
        acc_text = self.sections['accomplishments']
        if acc_text:
            bullets = [line.strip() for line in acc_text.split('\n') 
                      if line.strip() and len(line.strip()) > 20]
            achievements.extend(bullets[:3])
        
        # From experience section
        exp_text = self.sections['experience']
        if exp_text:
            bullets = [line.strip() for line in exp_text.split('\n') 
                      if line.strip() and len(line.strip()) > 30]
            achievements.extend(bullets[:2])
        
        return achievements[:5]
    
    def extract_skills(self):
        """Extract skills list"""
        skills_text = self.sections['skills']
        if skills_text:
            skills = [s.strip() for s in skills_text.split(',') if s.strip()]
            return skills
        return []
    
    def extract_job_responsibilities(self):
        """Extract job responsibility examples"""
        exp_text = self.sections['experience']
        if exp_text:
            paragraphs = exp_text.split('\n\n')
            if paragraphs:
                first_job = paragraphs[0]
                lines = [line.strip() for line in first_job.split('\n') 
                        if line.strip() and len(line.strip()) > 40]
                return lines[:3]
        return []


class PDFImporter:
    """Import PDFs and create knowledge base entries"""
    
    def __init__(self):
        print("Loading embedding model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✅ Embedding model loaded!")
    
    def process_all_pdfs(self):
        """Process all PDFs from dataset"""
        categories = os.listdir(PDF_BASE_PATH)
        total_entries = 0
        
        print(f"\n{'='*80}")
        print(f"Starting PDF Import: {len(categories)} categories, 2,484 PDFs")
        print(f"{'='*80}\n")
        
        for category in sorted(categories):
            category_path = os.path.join(PDF_BASE_PATH, category)
            
            if not os.path.isdir(category_path):
                continue
            
            pdf_files = [f for f in os.listdir(category_path) if f.endswith('.pdf')]
            
            print(f"\n📂 Processing {category}: {len(pdf_files)} PDFs")
            
            category_entries = 0
            
            for pdf_file in tqdm(pdf_files, desc=category, leave=True):
                pdf_path = os.path.join(category_path, pdf_file)
                
                try:
                    # Extract text from PDF
                    with pdfplumber.open(pdf_path) as pdf:
                        text = ""
                        for page in pdf.pages:
                            page_text = page.extract_text()
                            if page_text:
                                text += page_text + "\n"
                    
                    if not text.strip():
                        continue
                    
                    # Parse resume
                    parser = ResumeParser(text, category)
                    
                    # Create knowledge base entries
                    kb_entries = self._create_kb_entries(parser, category, pdf_file)
                    
                    # Store in database
                    for entry in kb_entries:
                        kb_entry = KnowledgeBase(**entry)
                        kb_entry.save()
                        category_entries += 1
                        total_entries += 1
                
                except Exception as e:
                    continue
            
            print(f"✅ {category}: Created {category_entries} KB entries\n")
        
        print(f"\n{'='*80}")
        print(f"✅ IMPORT COMPLETE!")
        print(f"{'='*80}")
        print(f"Total KB Entries Created: {total_entries}")
        print(f"{'='*80}\n")
        
        return total_entries
    
    def _create_kb_entries(self, parser, category, pdf_file):
        """Create multiple KB entries from parsed resume"""
        entries = []
        
        try:
            # 1. Professional Summary Entry
            summary = parser.extract_summary()
            if summary and len(summary) > 10:
                embedding = self.embedding_model.encode(summary)
                entries.append({
                    'title': f"{category} Summary",
                    'content': summary,
                    'category': 'summary',
                    'role_type': self._map_role_type(category),
                    'industry': category.lower(),
                    'embedding_vector': ','.join([str(float(x)) for x in embedding])
                })
            
            # 2. Achievement Entries
            achievements = parser.extract_achievements()
            for idx, achievement in enumerate(achievements[:2]):
                if achievement and len(achievement) > 20:
                    try:
                        embedding = self.embedding_model.encode(achievement)
                        entries.append({
                            'title': f"{category} Achievement",
                            'content': achievement,
                            'category': 'achievement',
                            'role_type': self._map_role_type(category),
                            'industry': category.lower(),
                            'embedding_vector': ','.join([str(float(x)) for x in embedding])
                        })
                    except:
                        pass
            
            # 3. Skills Entry
            skills = parser.extract_skills()
            if skills:
                skills_text = ', '.join(skills[:15])
                if len(skills_text) > 10:
                    embedding = self.embedding_model.encode(skills_text)
                    entries.append({
                        'title': f"{category} Skills",
                        'content': skills_text,
                        'category': 'skill',
                        'role_type': self._map_role_type(category),
                        'industry': category.lower(),
                        'embedding_vector': ','.join([str(float(x)) for x in embedding])
                    })
            
            # 4. Job Responsibility Entry
            responsibilities = parser.extract_job_responsibilities()
            if responsibilities:
                resp_text = ' '.join(responsibilities)
                if len(resp_text) > 20:
                    embedding = self.embedding_model.encode(resp_text)
                    entries.append({
                        'title': f"{category} Responsibility",
                        'content': resp_text,
                        'category': 'best_practice',
                        'role_type': self._map_role_type(category),
                        'industry': category.lower(),
                        'embedding_vector': ','.join([str(float(x)) for x in embedding])
                    })
        except Exception as e:
            print(f"Error creating KB entries: {e}")
        
        return entries
    
    def _map_role_type(self, category):
        """Map category to role_type"""
        mapping = {
            'INFORMATION-TECHNOLOGY': 'backend_developer',
            'ENGINEERING': 'backend_developer',
            'FINANCE': 'backend_developer',
            'DESIGNER': 'designer',
            'DIGITAL-MEDIA': 'designer',
            'HR': 'manager',
            'BUSINESS-DEVELOPMENT': 'manager',
            'SALES': 'manager',
            'CONSULTANT': 'manager',
            'PUBLIC-RELATIONS': 'manager',
        }
        return mapping.get(category, 'general')


def main():
    """Main execution"""
    print("\n" + "="*80)
    print("Starting Resume PDF to Knowledge Base Import")
    print("="*80 + "\n")
    
    importer = PDFImporter()
    total = importer.process_all_pdfs()
    
    print(f"\n✅ Successfully created {total} knowledge base entries!")
    print(f"✅ Knowledge base is ready for RAG system!\n")


if __name__ == "__main__":
    main()