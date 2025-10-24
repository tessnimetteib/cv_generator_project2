"""
CV Generator Models
==================

Complete data models for CV generation with RAG support.
Includes profession, cv_section, and content_type fields for advanced RAG filtering.
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import URLValidator
import json


class KnowledgeBase(models.Model):
    """
    Enhanced Knowledge Base with profession and section filtering.
    
    Features:
    ✅ 11,215+ professional CV entries
    ✅ Profession-specific filtering (Accountant, Backend Dev, etc.)
    ✅ CV section filtering (Summary, Experience, Skills, etc.)
    ✅ Content type classification (Bullet, Paragraph, Full Job Description)
    ✅ Embedding vectors for semantic search
    """
    
    PROFESSION_CHOICES = [
        ('Accountant', 'Accountant'),
        ('Accounts Payable Specialist', 'Accounts Payable Specialist'),
        ('Financial Analyst', 'Financial Analyst'),
        ('Backend Developer', 'Backend Developer'),
        ('Frontend Developer', 'Frontend Developer'),
        ('Full Stack Developer', 'Full Stack Developer'),
        ('DevOps Engineer', 'DevOps Engineer'),
        ('Data Scientist', 'Data Scientist'),
        ('Data Engineer', 'Data Engineer'),
        ('Manager', 'Manager'),
        ('Project Manager', 'Project Manager'),
        ('Product Manager', 'Product Manager'),
        ('QA Engineer', 'QA Engineer'),
        ('Systems Administrator', 'Systems Administrator'),
        ('Network Engineer', 'Network Engineer'),
        ('Security Engineer', 'Security Engineer'),
        ('Cloud Architect', 'Cloud Architect'),
        ('Software Architect', 'Software Architect'),
        ('Business Analyst', 'Business Analyst'),
        ('UX/UI Designer', 'UX/UI Designer'),
        ('Marketing Manager', 'Marketing Manager'),
        ('Sales Manager', 'Sales Manager'),
        ('HR Manager', 'HR Manager'),
        ('General', 'General'),
    ]
    
    CV_SECTION_CHOICES = [
        ('summary', 'Professional Summary'),
        ('experience', 'Experience Description'),
        ('achievement', 'Achievement Bullet'),
        ('responsibility', 'Job Responsibility'),
        ('skill', 'Skill'),
        ('education', 'Education'),
        ('certification', 'Certification'),
        ('award', 'Award/Recognition'),
        ('project', 'Project Description'),
    ]
    
    CONTENT_TYPE_CHOICES = [
        ('bullet', 'Single Bullet Point'),
        ('paragraph', 'Full Paragraph'),
        ('job_description', 'Complete Job Description'),
        ('achievement', 'Achievement Statement'),
    ]
    
    # Core fields
    title = models.CharField(
        max_length=300,
        help_text="Title/heading of the KB entry"
    )
    content = models.TextField(
        help_text="Full content of the KB entry"
    )
    
    # RAG Enhancement Fields (NEW!)
    profession = models.CharField(
        max_length=100,
        choices=PROFESSION_CHOICES,
        default='General',
        db_index=True,
        help_text="Target profession for this entry"
    )
    
    cv_section = models.CharField(
        max_length=50,
        choices=CV_SECTION_CHOICES,
        default='achievement',
        db_index=True,
        help_text="Which CV section this applies to"
    )
    
    content_type = models.CharField(
        max_length=50,
        choices=CONTENT_TYPE_CHOICES,
        default='bullet',
        help_text="Type of content (bullet, paragraph, etc.)"
    )
    
    # Original fields
    category = models.CharField(
        max_length=100,
        db_index=True,
        help_text="General category"
    )
    role_type = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Type of role"
    )
    industry = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        help_text="Industry/sector"
    )
    
    # Embedding & Metadata
    embedding_vector = models.TextField(
        help_text="384-dimensional embedding vector (JSON format)"
    )
    confidence_score = models.FloatField(
        default=1.0,
        help_text="Confidence score (0-1) for this entry"
    )
    word_count = models.IntegerField(
        default=0,
        help_text="Number of words in content"
    )
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    source_document = models.CharField(
        max_length=255,
        blank=True,
        help_text="Source PDF or document"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['profession', 'cv_section']),
            models.Index(fields=['profession', 'category']),
            models.Index(fields=['cv_section', 'category']),
        ]
    
    def __str__(self):
        return f"{self.profession} - {self.get_cv_section_display()}: {self.title[:50]}"
    
    def get_embedding_vector(self):
        """Parse embedding vector from JSON"""
        try:
            return json.loads(self.embedding_vector)
        except:
            return None
    
    def set_embedding_vector(self, vector):
        """Store embedding vector as JSON"""
        self.embedding_vector = json.dumps(vector.tolist() if hasattr(vector, 'tolist') else vector)
    
    def get_word_count(self):
        """Calculate word count"""
        return len(self.content.split())


class CVDocument(models.Model):
    """
    User's CV Document
    
    Stores user information and tracks generated content.
    """
    
    PROFESSION_CHOICES = KnowledgeBase.PROFESSION_CHOICES
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cv_documents')
    
    # Personal Information
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    location = models.CharField(max_length=255)
    professional_headline = models.CharField(
        max_length=255,
        help_text="e.g., Senior Backend Developer"
    )
    professional_summary = models.TextField(blank=True)
    
    # Professional Details
    profession = models.CharField(
        max_length=100,
        choices=PROFESSION_CHOICES,
        default='General',
        db_index=True,
        help_text="User's profession for targeted RAG retrieval"
    )
    years_of_experience = models.IntegerField(default=0)
    
    # Generated Content
    generated_summary = models.TextField(
        blank=True,
        help_text="AI-generated professional summary"
    )
    generated_cv_content = models.JSONField(
        default=dict,
        blank=True,
        help_text="Complete generated CV content"
    )
    is_generated = models.BooleanField(default=False)
    generated_at = models.DateTimeField(null=True, blank=True)
    
    # Tracking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.full_name} - {self.profession}"


class Skill(models.Model):
    """User's Skills"""
    
    PROFICIENCY_CHOICES = [
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
        ('Expert', 'Expert'),
    ]
    
    cv_document = models.ForeignKey(CVDocument, on_delete=models.CASCADE, related_name='skills')
    skill_name = models.CharField(max_length=100)
    category = models.CharField(max_length=100, blank=True)  # Technical, Soft, Tools, etc.
    proficiency_level = models.CharField(max_length=20, choices=PROFICIENCY_CHOICES, default='Intermediate')
    years_of_experience = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.skill_name} ({self.proficiency_level})"


class WorkExperience(models.Model):
    """User's Work Experience"""
    
    cv_document = models.ForeignKey(CVDocument, on_delete=models.CASCADE, related_name='work_experiences')
    
    job_title = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True)
    
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    
    job_description = models.TextField(blank=True)
    achievements = models.TextField(blank=True)
    technologies = models.CharField(max_length=500, blank=True)  # Comma-separated
    
    generated_description = models.TextField(
        blank=True,
        help_text="AI-generated job description"
    )
    generated_bullets = models.JSONField(
        default=list,
        blank=True,
        help_text="AI-generated achievement bullets"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.job_title} at {self.company_name}"


class Education(models.Model):
    """User's Education"""
    
    cv_document = models.ForeignKey(CVDocument, on_delete=models.CASCADE, related_name='education')
    
    institution = models.CharField(max_length=255)
    degree = models.CharField(max_length=100)
    field_of_study = models.CharField(max_length=100)
    graduation_date = models.DateField()
    gpa = models.CharField(max_length=10, blank=True)
    honors = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    
    generated_description = models.TextField(
        blank=True,
        help_text="AI-generated education description"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.degree} in {self.field_of_study}"


class CVGenerationFeedback(models.Model):
    """
    Feedback on generated CV content
    
    Used for feedback loops and continuous improvement.
    """
    
    RATING_CHOICES = [
        (1, '⭐ Poor'),
        (2, '⭐⭐ Fair'),
        (3, '⭐⭐⭐ Good'),
        (4, '⭐⭐⭐⭐ Very Good'),
        (5, '⭐⭐⭐⭐⭐ Excellent'),
    ]
    
    cv_document = models.ForeignKey(CVDocument, on_delete=models.CASCADE, related_name='feedback')
    
    section_type = models.CharField(
        max_length=50,
        choices=KnowledgeBase.CV_SECTION_CHOICES,
        help_text="Which section the feedback is about"
    )
    
    generated_content = models.TextField(
        help_text="The generated content being rated"
    )
    
    rating = models.IntegerField(
        choices=RATING_CHOICES,
        help_text="User's rating 1-5"
    )
    
    feedback_text = models.TextField(
        blank=True,
        help_text="Optional user feedback/comments"
    )
    
    was_helpful = models.BooleanField(
        default=True,
        help_text="Did user find this helpful?"
    )
    
    suggested_improvement = models.TextField(
        blank=True,
        help_text="What could be improved?"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.cv_document.full_name} - {self.section_type} ({self.rating}/5)"


class RAGCache(models.Model):
    """
    Cache for RAG queries to improve performance
    
    Stores similar results for repeated queries.
    """
    
    profession = models.CharField(max_length=100, db_index=True)
    cv_section = models.CharField(max_length=50, db_index=True)
    query_hash = models.CharField(max_length=64, unique=True, db_index=True)
    query_text = models.TextField()
    
    cached_results = models.JSONField()
    hit_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    accessed_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Cache: {self.profession} - {self.cv_section}"