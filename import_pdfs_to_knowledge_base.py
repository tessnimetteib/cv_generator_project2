# -*- coding: utf-8 -*-
import os
import sys
import django

# Setup Django BEFORE imports
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cv_analyzer.settings')
django.setup()

import pdfplumber
from sentence_transformers import SentenceTransformer
from cv_gen.models import KnowledgeBase
import re
from tqdm import tqdm
import json

PDF_BASE_PATH = r"C:\Users\DELL\Desktop\resume_dataset\data\data"

# Mapping of folder names to professions
PROFESSION_MAPPING = {
    'ACCOUNTANT': 'Accountant',
    'ADVOCATE': 'Advocate',
    'AGRICULTURE': 'Agriculture',
    'APPAREL': 'Apparel',
    'ARTS': 'Arts',
    'AUTOMOBILE': 'Automobile',
    'AVIATION': 'Aviation',
    'BANKING': 'Banking',
    'BPO': 'BPO',
    'BUSINESS-DEVELOPMENT': 'Business Development',
    'CHEF': 'Chef',
    'CONSTRUCTION': 'Construction',
    'CONSULTANT': 'Consultant',
    'DESIGNER': 'Designer',
    'DIGITAL-MEDIA': 'Digital Media',
    'ENGINEERING': 'Engineering',
    'FINANCE': 'Finance',
    'FITNESS': 'Fitness',
    'HEALTHCARE': 'Healthcare',
    'HR': 'HR',
    'INFORMATION-TECHNOLOGY': 'Backend Developer',  # Map IT to Backend Developer
    'PUBLIC-RELATIONS': 'Public Relations',
    'SALES': 'Sales',
    'TEACHER': 'Teacher',
}


class ResumeParser:
    """Parse resume PDF text"""
    
    def __init__(self, text, category):
        self.text = text
        self.category = category
        self.sections = self._parse_sections()
    
    def _parse_sections(self):
        """Extract main sections"""
        sections = {
            'summary': '',
            'experience': '',
            'education': '',
            'skills': '',
            'accomplishments': ''
        }
        
        summary_match = re.search(r'Summary\s*(.*?)(?=Experience|Education|Skills|Highlights|$)', 
                                 self.text, re.DOTALL | re.IGNORECASE)
        if summary_match:
            sections['summary'] = summary_match.group(1).strip()
        
        exp_match = re.search(r'Experience\s*(.*?)(?=Education|Skills|$)', 
                             self.text, re.DOTALL | re.IGNORECASE)
        if exp_match:
            sections['experience'] = exp_match.group(1).strip()
        
        edu_match = re.search(r'Education\s*(.*?)(?=Skills|$)', 
                             self.text, re.DOTALL | re.IGNORECASE)
        if edu_match:
            sections['education'] = edu_match.group(1).strip()
        
        skills_match = re.search(r'Skills\s*(.*?)(?=$)', 
                                self.text, re.DOTALL | re.IGNORECASE)
        if skills_match:
            sections['skills'] = skills_match.group(1).strip()
        
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
        """Extract achievements"""
        achievements = []
        acc_text = self.sections['accomplishments']
        if acc_text:
            bullets = [line.strip() for line in acc_text.split('\n') 
                      if line.strip() and len(line.strip()) > 20]
            achievements.extend(bullets[:3])
        
        exp_text = self.sections['experience']
        if exp_text:
            bullets = [line.strip() for line in exp_text.split('\n') 
                      if line.strip() and len(line.strip()) > 30]
            achievements.extend(bullets[:2])
        
        return achievements[:5]
    
    def extract_skills(self):
        """Extract skills"""
        skills_text = self.sections['skills']
        if skills_text:
            skills = [s.strip() for s in skills_text.split(',') if s.strip()]
            return skills
        return []


class PDFImporter:
    """Import PDFs and create KB entries"""
    
    def __init__(self):
        print("Loading embedding model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✅ Embedding model loaded!")
    
    def process_all_pdfs(self):
        """Process all PDFs"""
        categories = os.listdir(PDF_BASE_PATH)
        total_entries = 0
        
        print(f"\n{'='*80}")
        print(f"Starting PDF Import")
        print(f"{'='*80}\n")
        
        for category in sorted(categories):
            category_path = os.path.join(PDF_BASE_PATH, category)
            
            if not os.path.isdir(category_path):
                continue
            
            pdf_files = [f for f in os.listdir(category_path) if f.endswith('.pdf')]
            
            if not pdf_files:
                continue
            
            print(f"\n📂 Processing {category}: {len(pdf_files)} PDFs")
            
            category_entries = 0
            
            for pdf_file in tqdm(pdf_files, desc=category, leave=True):
                pdf_path = os.path.join(category_path, pdf_file)
                
                try:
                    with pdfplumber.open(pdf_path) as pdf:
                        text = ""
                        for page in pdf.pages:
                            page_text = page.extract_text()
                            if page_text:
                                text += page_text + "\n"
                    
                    if not text.strip():
                        continue
                    
                    parser = ResumeParser(text, category)
                    kb_entries = self._create_kb_entries(parser, category, pdf_file)
                    
                    for entry in kb_entries:
                        kb_entry = KnowledgeBase(**entry)
                        kb_entry.save()
                        category_entries += 1
                        total_entries += 1
                
                except Exception as e:
                    continue
            
            print(f"✅ {category}: Created {category_entries} KB entries\n")
        
        print(f"\n{'='*80}")
        print(f"✅ IMPORT COMPLETE! Total: {total_entries}")
        print(f"{'='*80}\n")
        
        return total_entries
    
    def _create_kb_entries(self, parser, category, pdf_file):
        """Create KB entries with correct profession"""
        entries = []
        
        # Get profession from mapping
        profession = PROFESSION_MAPPING.get(category, 'General')
        
        try:
            summary = parser.extract_summary()
            if summary and len(summary) > 10:
                embedding = self.embedding_model.encode(summary)
                entries.append({
                    'title': f"{category} Summary",
                    'content': summary,
                    'category': 'summary',
                    'profession': profession,  # ✅ USE MAPPED PROFESSION
                    'cv_section': 'summary',
                    'embedding_vector': json.dumps(embedding.tolist())
                })
            
            achievements = parser.extract_achievements()
            for achievement in achievements[:2]:
                if achievement and len(achievement) > 20:
                    try:
                        embedding = self.embedding_model.encode(achievement)
                        entries.append({
                            'title': f"{category} Achievement",
                            'content': achievement,
                            'category': 'achievement',
                            'profession': profession,  # ✅ USE MAPPED PROFESSION
                            'cv_section': 'achievement',
                            'embedding_vector': json.dumps(embedding.tolist())
                        })
                    except:
                        pass
            
            skills = parser.extract_skills()
            if skills:
                skills_text = ', '.join(skills[:15])
                if len(skills_text) > 10:
                    embedding = self.embedding_model.encode(skills_text)
                    entries.append({
                        'title': f"{category} Skills",
                        'content': skills_text,
                        'category': 'skill',
                        'profession': profession,  # ✅ USE MAPPED PROFESSION
                        'cv_section': 'skill',
                        'embedding_vector': json.dumps(embedding.tolist())
                    })
        except Exception as e:
            pass
        
        return entries


def main():
    """Main execution"""
    print("\n" + "="*80)
    print("Resume PDF to Knowledge Base Import (WITH PROFESSION MAPPING)")
    print("="*80 + "\n")
    
    importer = PDFImporter()
    total = importer.process_all_pdfs()
    
    print(f"\n✅ Successfully created {total} KB entries!\n")


if __name__ == "__main__":
    main()