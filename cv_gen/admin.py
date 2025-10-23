from django.contrib import admin
from .models import (
    CVDocument,
    WorkExperience,
    Education,
    Skill,
    KnowledgeBase
)

@admin.register(CVDocument)
class CVDocumentAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'professional_headline', 'is_generated', 'created_at')
    list_filter = ('is_generated', 'created_at')
    search_fields = ('full_name', 'email')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(WorkExperience)
class WorkExperienceAdmin(admin.ModelAdmin):
    list_display = ('job_title', 'company_name', 'start_date', 'is_current')
    list_filter = ('is_current', 'start_date')
    search_fields = ('job_title', 'company_name')

@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ('degree', 'institution', 'graduation_date')
    search_fields = ('degree', 'institution')

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('skill_name', 'category', 'proficiency_level')
    list_filter = ('category', 'proficiency_level')
    search_fields = ('skill_name',)

@admin.register(KnowledgeBase)
class KnowledgeBaseAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'role_type', 'industry')
    list_filter = ('category', 'role_type', 'industry')
    search_fields = ('title', 'content')