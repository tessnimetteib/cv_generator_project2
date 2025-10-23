from django.db import models
from django.contrib.auth.models import User
import json

class CVDocument(models.Model):
    """Main CV document model"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Personal Information
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    location = models.CharField(max_length=200)
    professional_headline = models.CharField(max_length=200)
    professional_summary = models.TextField(blank=True)
    
    # Generated Content
    generated_summary = models.TextField(blank=True)
    generated_cv_content = models.TextField(blank=True)
    
    # Status
    is_generated = models.BooleanField(default=False)
    cv_format = models.CharField(
        max_length=10,
        choices=[('HTML', 'HTML'), ('PDF', 'PDF'), ('DOCX', 'DOCX')],
        default='HTML'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.full_name} - {self.created_at.strftime('%Y-%m-%d')}"
    
    class Meta:
        ordering = ['-created_at']


class WorkExperience(models.Model):
    """Work experience entries"""
    cv_document = models.ForeignKey(
        CVDocument,
        on_delete=models.CASCADE,
        related_name='work_experiences'
    )
    
    job_title = models.CharField(max_length=200)
    company_name = models.CharField(max_length=200)
    location = models.CharField(max_length=200, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    
    # Raw input
    job_description = models.TextField()
    achievements = models.TextField()
    technologies = models.TextField()  # Comma-separated
    
    # Generated content
    generated_bullets = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.job_title} at {self.company_name}"
    
    class Meta:
        ordering = ['-start_date']


class Education(models.Model):
    """Education entries"""
    cv_document = models.ForeignKey(
        CVDocument,
        on_delete=models.CASCADE,
        related_name='education_entries'
    )
    
    institution = models.CharField(max_length=200)
    degree = models.CharField(max_length=100)
    field_of_study = models.CharField(max_length=200)
    graduation_date = models.DateField()
    gpa = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True
    )
    honors = models.CharField(max_length=200, blank=True)
    relevant_coursework = models.TextField(blank=True)
    
    # Generated content
    generated_section = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.degree} from {self.institution}"
    
    class Meta:
        ordering = ['-graduation_date']


class Skill(models.Model):
    """Skills storage"""
    SKILL_CATEGORIES = [
        ('Technical', 'Technical'),
        ('Soft', 'Soft Skill'),
        ('Language', 'Language'),
        ('Certification', 'Certification'),
    ]
    
    PROFICIENCY_LEVELS = [
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
        ('Expert', 'Expert'),
    ]
    
    cv_document = models.ForeignKey(
        CVDocument,
        on_delete=models.CASCADE,
        related_name='skills'
    )
    
    skill_name = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=SKILL_CATEGORIES)
    proficiency_level = models.CharField(
        max_length=20,
        choices=PROFICIENCY_LEVELS,
        default='Intermediate'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.skill_name
    
    class Meta:
        ordering = ['category', 'skill_name']


class KnowledgeBase(models.Model):
    """Knowledge base entries for RAG"""
    title = models.CharField(max_length=300)
    content = models.TextField()
    category = models.CharField(
        max_length=100,
        choices=[
            ('achievement', 'Achievement Example'),
            ('summary', 'Summary Example'),
            ('skill', 'Skill Description'),
            ('best_practice', 'Best Practice'),
        ]
    )
    role_type = models.CharField(
        max_length=100,
        choices=[
            ('backend_developer', 'Backend Developer'),
            ('frontend_developer', 'Frontend Developer'),
            ('manager', 'Manager'),
            ('designer', 'Designer'),
            ('general', 'General'),
        ],
        default='general'
    )
    industry = models.CharField(max_length=100, default='general')
    
    embedding_vector = models.TextField(blank=True)  # Store as JSON string
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']