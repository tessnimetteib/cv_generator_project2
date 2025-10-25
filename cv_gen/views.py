"""
CV Generator Views
==================

Complete web interface for CV generation.
"""

import logging
import json
import textwrap
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse, FileResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from django.contrib import messages
from datetime import date
from io import BytesIO

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

from .models import CVDocument, Skill, WorkExperience, Education
from .services.generation_service import CVGenerationService

logger = logging.getLogger(__name__)


def home(request):
    """Home page - Public"""
    try:
        user_cvs = 0
        if request.user.is_authenticated:
            user_cvs = CVDocument.objects.filter(user=request.user).count()
        context = {'user_cvs': user_cvs}
        return render(request, 'cv_gen/home.html', context)
    except Exception as e:
        logger.error(f"Error in home: {e}")
        return render(request, 'cv_gen/home.html', {'error': str(e)})


def signup(request):
    """User signup"""
    try:
        if request.method == 'POST':
            username = request.POST.get('username', '').strip()
            email = request.POST.get('email', '').strip()
            password1 = request.POST.get('password1', '')
            password2 = request.POST.get('password2', '')
            if not username or not email or not password1 or not password2:
                messages.error(request, "❌ All fields are required!")
                return render(request, 'cv_gen/signup.html')
            if len(password1) < 6:
                messages.error(request, "❌ Password must be at least 6 characters!")
                return render(request, 'cv_gen/signup.html')
            if password1 != password2:
                messages.error(request, "❌ Passwords don't match!")
                return render(request, 'cv_gen/signup.html')
            if User.objects.filter(username=username).exists():
                messages.error(request, "❌ Username already taken!")
                return render(request, 'cv_gen/signup.html')
            if User.objects.filter(email=email).exists():
                messages.error(request, "❌ Email already registered!")
                return render(request, 'cv_gen/signup.html')
            user = User.objects.create_user(username=username, email=email, password=password1)
            logger.info(f"✅ New user created: {username}")
            messages.success(request, "✅ Account created successfully! Please login.")
            return redirect('login')
        return render(request, 'cv_gen/signup.html')
    except Exception as e:
        logger.error(f"Error in signup: {e}")
        messages.error(request, f"❌ Error: {str(e)}")
        return render(request, 'cv_gen/signup.html', {'error': str(e)})


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
        messages.error(request, "Error loading CVs")
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

            # --- AI Generation after creating the CV ---
            try:
                CVGenerationService().generate_complete_cv(cv)
                logger.info("AI generation complete after CV creation")
            except Exception as e:
                logger.error(f"AI generation failed after CV creation: {e}")

            messages.success(request, f"✅ CV '{full_name}' created successfully!")
            return redirect('cv_gen:cv_preview', cv_id=cv.id)

        professions = CVDocument.PROFESSION_CHOICES
        return render(request, 'cv_gen/cv_form.html', {
            'professions': professions,
            'cv': None
        })

    except Exception as e:
        logger.error(f"Error in cv_create: {e}")
        messages.error(request, f"Error creating CV: {str(e)}")
        return render(request, 'cv_gen/cv_form.html', {'error': str(e)})


@login_required
def cv_edit(request, cv_id):
    """Edit CV"""
    try:
        cv = get_object_or_404(CVDocument, id=cv_id, user=request.user)
        if request.method == 'POST':
            cv.full_name = request.POST.get('full_name', cv.full_name)
            cv.email = request.POST.get('email', cv.email)
            cv.phone = request.POST.get('phone', cv.phone)
            cv.location = request.POST.get('location', cv.location)
            cv.professional_headline = request.POST.get('professional_headline', cv.professional_headline)
            cv.profession = request.POST.get('profession', cv.profession)
            cv.professional_summary = request.POST.get('professional_summary', cv.professional_summary)
            cv.save()
            logger.info(f"Updated CV: {cv.id}")
            messages.success(request, "✅ CV updated successfully!")
            return redirect('cv_gen:cv_preview', cv_id=cv.id)
        context = {
            'cv': cv,
            'professions': CVDocument.PROFESSION_CHOICES,
        }
        return render(request, 'cv_gen/cv_edit.html', context)
    except Exception as e:
        logger.error(f"Error in cv_edit: {e}")
        messages.error(request, "Error updating CV")
        return render(request, 'cv_gen/cv_edit.html', {'error': str(e)})


@login_required
def cv_preview(request, cv_id):
    """Preview and generate CV"""
    try:
        cv = get_object_or_404(CVDocument, id=cv_id, user=request.user)
        # Allow manual AI generation with a button
        if request.method == 'POST' and request.POST.get('action') == 'generate':
            logger.info(f"Manual AI generation triggered for CV: {cv.id}")
            try:
                CVGenerationService().generate_complete_cv(cv)
                messages.success(request, "✅ AI-powered content generated!")
                cv.refresh_from_db()
            except Exception as e:
                logger.error(f"AI generation failed on preview: {e}")
                messages.error(request, f"❌ AI generation failed: {e}")

        # Get all data
        skills = cv.skills.all()
        work_experiences = []
        for exp in cv.work_experiences.all():
            exp.bullets_list = exp.generated_bullets.split("\n") if exp.generated_bullets else []
            work_experiences.append(exp)
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
        messages.error(request, f"Error: {str(e)}")
        return redirect('cv_gen:cv_list')


@login_required
def cv_download(request, cv_id):
    """Download CV as PDF"""
    try:
        cv = get_object_or_404(CVDocument, id=cv_id, user=request.user)
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        y = height - 0.5 * inch
        # HEADER SECTION
        c.setFont("Helvetica-Bold", 24)
        c.drawString(0.5 * inch, y, cv.full_name)
        y -= 0.3 * inch
        c.setFont("Helvetica-Bold", 14)
        c.drawString(0.5 * inch, y, cv.professional_headline)
        y -= 0.2 * inch
        c.setFont("Helvetica", 10)
        contact_info = []
        if cv.email:
            contact_info.append(cv.email)
        if cv.phone:
            contact_info.append(cv.phone)
        if cv.location:
            contact_info.append(cv.location)
        contact_text = " | ".join(contact_info)
        c.drawString(0.5 * inch, y, contact_text)
        y -= 0.3 * inch
        # PROFESSIONAL SUMMARY
        if cv.generated_summary:
            c.setFont("Helvetica-Bold", 12)
            c.drawString(0.5 * inch, y, "Professional Summary")
            y -= 0.2 * inch
            c.setFont("Helvetica", 10)
            summary_lines = cv.generated_summary.split('\n')
            for line in summary_lines[:8]:
                if line.strip():
                    wrapped_lines = textwrap.wrap(line.strip(), width=85)
                    for wrapped_line in wrapped_lines:
                        if y < 0.5 * inch:
                            c.showPage()
                            y = height - 0.5 * inch
                        c.drawString(0.5 * inch, y, wrapped_line)
                        y -= 0.15 * inch
            y -= 0.15 * inch
        # WORK EXPERIENCE
        if cv.work_experiences.exists():
            c.setFont("Helvetica-Bold", 12)
            c.drawString(0.5 * inch, y, "Work Experience")
            y -= 0.2 * inch
            for exp in cv.work_experiences.all()[:5]:
                c.setFont("Helvetica-Bold", 10)
                job_info = f"{exp.job_title}"
                if exp.company_name:
                    job_info += f" - {exp.company_name}"
                if y < 0.7 * inch:
                    c.showPage()
                    y = height - 0.5 * inch
                c.drawString(0.5 * inch, y, job_info)
                y -= 0.15 * inch
                c.setFont("Helvetica", 9)
                if exp.start_date:
                    date_str = f"{exp.start_date.strftime('%b %Y')} - "
                    if exp.is_current:
                        date_str += "Present"
                    elif exp.end_date:
                        date_str += exp.end_date.strftime('%b %Y')
                    c.drawString(0.7 * inch, y, date_str)
                    y -= 0.12 * inch
                if exp.generated_bullets:
                    c.setFont("Helvetica", 9)
                    bullets = exp.generated_bullets.split('\n')[:4]
                    for bullet in bullets:
                        if bullet.strip():
                            wrapped = textwrap.wrap(bullet.strip(), width=80)
                            for line in wrapped:
                                if y < 0.5 * inch:
                                    c.showPage()
                                    y = height - 0.5 * inch
                                c.drawString(0.7 * inch, y, f"• {line}")
                                y -= 0.12 * inch
                y -= 0.1 * inch
        # SKILLS
        if cv.skills.exists():
            if y < 1.0 * inch:
                c.showPage()
                y = height - 0.5 * inch
            c.setFont("Helvetica-Bold", 12)
            c.drawString(0.5 * inch, y, "Skills")
            y -= 0.2 * inch
            c.setFont("Helvetica", 10)
            skills_list = ", ".join([s.skill_name for s in cv.skills.all()])
            wrapped_skills = textwrap.wrap(skills_list, width=85)
            for line in wrapped_skills:
                if y < 0.5 * inch:
                    c.showPage()
                    y = height - 0.5 * inch
                c.drawString(0.5 * inch, y, line)
                y -= 0.15 * inch
        c.save()
        buffer.seek(0)
        response = FileResponse(buffer, content_type='application/pdf')
        filename = f"{cv.full_name.replace(' ', '_')}_CV.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        logger.info(f"Downloaded CV: {cv.id}")
        messages.success(request, "✅ CV downloaded successfully!")
        return response
    except Exception as e:
        logger.error(f"Error downloading CV: {e}")
        messages.error(request, f"Error downloading PDF: {str(e)}")
        return redirect('cv_gen:cv_preview', cv_id=cv_id)


@login_required
def cv_delete(request, cv_id):
    """Delete a CV"""
    try:
        cv = get_object_or_404(CVDocument, id=cv_id, user=request.user)
        if request.method == 'POST':
            cv_name = cv.full_name
            cv.delete()
            logger.info(f"Deleted CV: {cv_name}")
            messages.success(request, f"✅ CV '{cv_name}' deleted successfully!")
            return redirect('cv_gen:cv_list')
        return render(request, 'cv_gen/cv_confirm_delete.html', {'cv': cv})
    except Exception as e:
        logger.error(f"Error in cv_delete: {e}")
        messages.error(request, "Error deleting CV")
        return redirect('cv_gen:cv_list')


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
        service = CVGenerationService()
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
            'message': '✅ Feedback saved! Thank you for helping us improve.' if success else '❌ Error saving feedback'
        })
    except Exception as e:
        logger.error(f"Error in cv_feedback: {e}")
        return JsonResponse({
            'success': False,
            'message': f'❌ Error: {str(e)}'
        })