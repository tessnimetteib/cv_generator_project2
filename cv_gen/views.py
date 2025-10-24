"""
CV Generator Views
==================

Complete web interface for CV generation.
"""

import logging
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from datetime import date

from .models import CVDocument, Skill, WorkExperience, Education
from .services.cv_generation_service import EnhancedCVGenerationService

logger = logging.getLogger(__name__)


@login_required
def cv_list(request):
    """List all user's CVs"""
    try:
        cvs = CVDocument.objects.filter(user=request.user).order_by('-created_at')
        
        context = {
            'cvs': cvs,
            'total_cvs': cvs.count(),
            'generated_cvs': cvs.filter(is_generated=True).count(),
        }
        
        return render(request, 'cv_gen/cv_list.html', context)
        
    except Exception as e:
        logger.error(f"Error in cv_list: {e}")
        return render(request, 'cv_gen/cv_list.html', {'error': str(e)})


@login_required
def cv_create(request):
    """Create new CV"""
    try:
        if request.method == 'POST':
            # Get form data
            full_name = request.POST.get('full_name')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            location = request.POST.get('location')
            professional_headline = request.POST.get('professional_headline')
            profession = request.POST.get('profession', 'General')
            professional_summary = request.POST.get('professional_summary', '')
            skills_text = request.POST.get('skills', '')
            
            # Create CV
            cv = CVDocument.objects.create(
                user=request.user,
                full_name=full_name,
                email=email,
                phone=phone,
                location=location,
                professional_headline=professional_headline,
                profession=profession,
                professional_summary=professional_summary,
            )
            
            logger.info(f"Created CV: {cv.id}")
            
            # Add skills
            if skills_text:
                for skill in skills_text.split(','):
                    skill = skill.strip()
                    if skill:
                        Skill.objects.create(
                            cv_document=cv,
                            skill_name=skill,
                            proficiency_level='Intermediate'
                        )
            
            # Add work experience if provided
            job_title = request.POST.get('job_title')
            if job_title:
                start_date = request.POST.get('start_date')
                try:
                    start_date = date.fromisoformat(start_date) if start_date else None
                except:
                    start_date = None
                
                WorkExperience.objects.create(
                    cv_document=cv,
                    job_title=job_title,
                    company_name=request.POST.get('company_name', ''),
                    location=request.POST.get('job_location', ''),
                    start_date=start_date,
                    job_description=request.POST.get('job_description', ''),
                )
            
            return redirect('cv_preview', cv_id=cv.id)
        
        # GET request - show form
        professions = CVDocument.PROFESSION_CHOICES
        return render(request, 'cv_gen/cv_form.html', {
            'professions': professions
        })
        
    except Exception as e:
        logger.error(f"Error in cv_create: {e}")
        return render(request, 'cv_gen/cv_form.html', {'error': str(e)})


@login_required
def cv_preview(request, cv_id):
    """Preview and generate CV"""
    try:
        cv = get_object_or_404(CVDocument, id=cv_id, user=request.user)
        
        # Check if generation was requested
        if request.method == 'POST' and request.POST.get('action') == 'generate':
            logger.info(f"Generating CV: {cv.id}")
            
            # Initialize service
            service = EnhancedCVGenerationService()
            
            # Generate full CV
            generated_content = service.generate_full_cv(cv)
            
            if generated_content:
                logger.info("CV generation successful")
                # Refresh from DB
                cv.refresh_from_db()
            else:
                logger.warning("CV generation failed")
        
        # Get all data
        skills = cv.skills.all()
        work_experiences = cv.work_experiences.all()
        education = cv.education.all()
        
        context = {
            'cv': cv,
            'skills': skills,
            'work_experiences': work_experiences,
            'education': education,
            'generated_content': cv.generated_cv_content,
            'is_generated': cv.is_generated,
        }
        
        return render(request, 'cv_gen/cv_preview.html', context)
        
    except Exception as e:
        logger.error(f"Error in cv_preview: {e}")
        return render(request, 'cv_gen/cv_preview.html', {'error': str(e)})


@login_required
def cv_edit(request, cv_id):
    """Edit CV"""
    try:
        cv = get_object_or_404(CVDocument, id=cv_id, user=request.user)
        
        if request.method == 'POST':
            # Update CV
            cv.full_name = request.POST.get('full_name', cv.full_name)
            cv.email = request.POST.get('email', cv.email)
            cv.phone = request.POST.get('phone', cv.phone)
            cv.location = request.POST.get('location', cv.location)
            cv.professional_headline = request.POST.get('professional_headline', cv.professional_headline)
            cv.profession = request.POST.get('profession', cv.profession)
            cv.professional_summary = request.POST.get('professional_summary', cv.professional_summary)
            cv.save()
            
            logger.info(f"Updated CV: {cv.id}")
            return redirect('cv_preview', cv_id=cv.id)
        
        context = {
            'cv': cv,
            'professions': CVDocument.PROFESSION_CHOICES,
        }
        
        return render(request, 'cv_gen/cv_edit.html', context)
        
    except Exception as e:
        logger.error(f"Error in cv_edit: {e}")
        return render(request, 'cv_gen/cv_edit.html', {'error': str(e)})


@login_required
@require_http_methods(["POST"])
def cv_feedback(request, cv_id):
    """Submit feedback on generated content"""
    try:
        cv = get_object_or_404(CVDocument, id=cv_id, user=request.user)
        
        section_type = request.POST.get('section_type')
        rating = int(request.POST.get('rating', 3))
        feedback_text = request.POST.get('feedback_text', '')
        suggested_improvement = request.POST.get('suggested_improvement', '')
        
        service = EnhancedCVGenerationService()
        success = service.collect_user_feedback(
            cv,
            section_type,
            rating,
            feedback_text,
            suggested_improvement
        )
        
        logger.info(f"Feedback submitted: {section_type} - rating {rating}/5")
        
        return JsonResponse({
            'success': success,
            'message': 'Feedback saved! Thank you for helping us improve.' if success else 'Error saving feedback'
        })
        
    except Exception as e:
        logger.error(f"Error in cv_feedback: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        })


@login_required
def cv_delete(request, cv_id):
    """Delete a CV"""
    try:
        cv = get_object_or_404(CVDocument, id=cv_id, user=request.user)
        
        if request.method == 'POST':
            cv_name = cv.full_name
            cv.delete()
            logger.info(f"Deleted CV: {cv_name}")
            return redirect('cv_list')
        
        return render(request, 'cv_gen/cv_confirm_delete.html', {'cv': cv})
        
    except Exception as e:
        logger.error(f"Error in cv_delete: {e}")
        return redirect('cv_list')


@login_required
def home(request):
    """Home page"""
    try:
        user_cvs = CVDocument.objects.filter(user=request.user).count()
        
        context = {
            'user_cvs': user_cvs,
        }
        
        return render(request, 'cv_gen/home.html', context)
        
    except Exception as e:
        logger.error(f"Error in home: {e}")
        return render(request, 'cv_gen/home.html', {'error': str(e)})