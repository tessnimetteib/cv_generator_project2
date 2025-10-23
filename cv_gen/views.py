from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from .models import (
    CVDocument,
    WorkExperience,
    Education,
    Skill,
    KnowledgeBase
)
from .forms import (
    PersonalInfoForm,
    WorkExperienceForm,
    EducationForm,
    SkillForm,
    BulkSkillsForm
)

@method_decorator(login_required, name='dispatch')
class CVDashboardView(View):
    """Dashboard showing all CVs"""
    
    def get(self, request):
        cvs = CVDocument.objects.filter(user=request.user)
        context = {
            'cvs': cvs,
            'total_cvs': cvs.count(),
            'generated_cvs': cvs.filter(is_generated=True).count()
        }
        return render(request, 'cv_gen/dashboard.html', context)

@method_decorator(login_required, name='dispatch')
class CVCreateView(View):
    """Create a new CV"""
    
    def get(self, request):
        form = PersonalInfoForm()
        context = {'form': form, 'step': 'personal_info'}
        return render(request, 'cv_gen/create_cv.html', context)
    
    def post(self, request):
        form = PersonalInfoForm(request.POST)
        if form.is_valid():
            cv = form.save(commit=False)
            cv.user = request.user
            cv.save()
            return redirect('cv_work_experience', pk=cv.pk)
        
        context = {'form': form, 'step': 'personal_info'}
        return render(request, 'cv_gen/create_cv.html', context)

@method_decorator(login_required, name='dispatch')
class AddWorkExperienceView(View):
    """Add work experience to CV"""
    
    def get(self, request, pk):
        cv = get_object_or_404(CVDocument, pk=pk, user=request.user)
        form = WorkExperienceForm()
        work_experiences = WorkExperience.objects.filter(cv_document=cv)
        
        context = {
            'cv': cv,
            'form': form,
            'work_experiences': work_experiences,
            'step': 'work_experience'
        }
        return render(request, 'cv_gen/add_work_experience.html', context)
    
    def post(self, request, pk):
        cv = get_object_or_404(CVDocument, pk=pk, user=request.user)
        form = WorkExperienceForm(request.POST)
        
        if form.is_valid():
            job = form.save(commit=False)
            job.cv_document = cv
            job.save()
            
            # Check if user clicks "Done" button
            if 'done' in request.POST:
                return redirect('cv_add_education', pk=cv.pk)
            else:
                return redirect('cv_work_experience', pk=cv.pk)
        
        work_experiences = WorkExperience.objects.filter(cv_document=cv)
        context = {
            'cv': cv,
            'form': form,
            'work_experiences': work_experiences,
            'step': 'work_experience'
        }
        return render(request, 'cv_gen/add_work_experience.html', context)

@method_decorator(login_required, name='dispatch')
class AddEducationView(View):
    """Add education to CV"""
    
    def get(self, request, pk):
        cv = get_object_or_404(CVDocument, pk=pk, user=request.user)
        form = EducationForm()
        educations = Education.objects.filter(cv_document=cv)
        
        context = {
            'cv': cv,
            'form': form,
            'educations': educations,
            'step': 'education'
        }
        return render(request, 'cv_gen/add_education.html', context)
    
    def post(self, request, pk):
        cv = get_object_or_404(CVDocument, pk=pk, user=request.user)
        form = EducationForm(request.POST)
        
        if form.is_valid():
            edu = form.save(commit=False)
            edu.cv_document = cv
            edu.save()
            
            if 'done' in request.POST:
                return redirect('cv_add_skills', pk=cv.pk)
            else:
                return redirect('cv_add_education', pk=cv.pk)
        
        educations = Education.objects.filter(cv_document=cv)
        context = {
            'cv': cv,
            'form': form,
            'educations': educations,
            'step': 'education'
        }
        return render(request, 'cv_gen/add_education.html', context)

@method_decorator(login_required, name='dispatch')
class AddSkillsView(View):
    """Add skills to CV"""
    
    def get(self, request, pk):
        cv = get_object_or_404(CVDocument, pk=pk, user=request.user)
        form = BulkSkillsForm()
        skills = Skill.objects.filter(cv_document=cv)
        
        context = {
            'cv': cv,
            'form': form,
            'skills': skills,
            'step': 'skills'
        }
        return render(request, 'cv_gen/add_skills.html', context)
    
    def post(self, request, pk):
        cv = get_object_or_404(CVDocument, pk=pk, user=request.user)
        form = BulkSkillsForm(request.POST)
        
        if form.is_valid():
            # Parse skills and create Skill objects
            technical_skills = [s.strip() for s in form.cleaned_data['technical_skills'].split(',') if s.strip()]
            soft_skills = [s.strip() for s in form.cleaned_data['soft_skills'].split(',') if s.strip()]
            languages = [s.strip() for s in form.cleaned_data['languages'].split(',') if s.strip()]
            certifications = [s.strip() for s in form.cleaned_data['certifications'].split(',') if s.strip()]
            
            # Create Skill objects
            for skill_name in technical_skills:
                Skill.objects.create(
                    cv_document=cv,
                    skill_name=skill_name,
                    category='Technical'
                )
            
            for skill_name in soft_skills:
                Skill.objects.create(
                    cv_document=cv,
                    skill_name=skill_name,
                    category='Soft'
                )
            
            for skill_name in languages:
                Skill.objects.create(
                    cv_document=cv,
                    skill_name=skill_name,
                    category='Language'
                )
            
            for skill_name in certifications:
                Skill.objects.create(
                    cv_document=cv,
                    skill_name=skill_name,
                    category='Certification'
                )
            
            return redirect('cv_generate', pk=cv.pk)
        
        skills = Skill.objects.filter(cv_document=cv)
        context = {
            'cv': cv,
            'form': form,
            'skills': skills,
            'step': 'skills'
        }
        return render(request, 'cv_gen/add_skills.html', context)

@method_decorator(login_required, name='dispatch')
class GenerateCVView(View):
    """Generate the CV"""
    
    def get(self, request, pk):
        cv = get_object_or_404(CVDocument, pk=pk, user=request.user)
        context = {'cv': cv}
        return render(request, 'cv_gen/generate_cv.html', context)
    
    def post(self, request, pk):
        cv = get_object_or_404(CVDocument, pk=pk, user=request.user)
        
        try:
            # For now, just mark as generated
            # We'll add LLM generation later
            cv.is_generated = True
            cv.generated_cv_content = "CV Generation Coming Soon - LLM Integration"
            cv.save()
            
            return redirect('cv_preview', pk=cv.pk)
        
        except Exception as e:
            context = {
                'cv': cv,
                'error': str(e)
            }
            return render(request, 'cv_gen/generate_cv.html', context)

@method_decorator(login_required, name='dispatch')
class CVPreviewView(View):
    """Preview generated CV"""
    
    def get(self, request, pk):
        cv = get_object_or_404(CVDocument, pk=pk, user=request.user)
        context = {'cv': cv}
        return render(request, 'cv_gen/preview_cv.html', context)

@method_decorator(login_required, name='dispatch')
class EditWorkExperienceView(View):
    """Edit work experience"""
    
    def get(self, request, cv_id, job_id):
        cv = get_object_or_404(CVDocument, pk=cv_id, user=request.user)
        job = get_object_or_404(WorkExperience, pk=job_id, cv_document=cv)
        form = WorkExperienceForm(instance=job)
        
        context = {
            'cv': cv,
            'form': form,
            'job': job
        }
        return render(request, 'cv_gen/edit_work_experience.html', context)
    
    def post(self, request, cv_id, job_id):
        cv = get_object_or_404(CVDocument, pk=cv_id, user=request.user)
        job = get_object_or_404(WorkExperience, pk=job_id, cv_document=cv)
        form = WorkExperienceForm(request.POST, instance=job)
        
        if form.is_valid():
            form.save()
            return redirect('cv_work_experience', pk=cv.pk)
        
        context = {
            'cv': cv,
            'form': form,
            'job': job
        }
        return render(request, 'cv_gen/edit_work_experience.html', context)

@login_required
def delete_work_experience(request, cv_id, job_id):
    """Delete work experience"""
    cv = get_object_or_404(CVDocument, pk=cv_id, user=request.user)
    job = get_object_or_404(WorkExperience, pk=job_id, cv_document=cv)
    job.delete()
    return redirect('cv_work_experience', pk=cv.pk)

@login_required
def delete_education(request, cv_id, edu_id):
    """Delete education"""
    cv = get_object_or_404(CVDocument, pk=cv_id, user=request.user)
    edu = get_object_or_404(Education, pk=edu_id, cv_document=cv)
    edu.delete()
    return redirect('cv_add_education', pk=cv.pk)

@login_required
def delete_skill(request, cv_id, skill_id):
    """Delete skill"""
    cv = get_object_or_404(CVDocument, pk=cv_id, user=request.user)
    skill = get_object_or_404(Skill, pk=skill_id, cv_document=cv)
    skill.delete()
    return redirect('cv_add_skills', pk=cv.pk)

@login_required
def download_cv_txt(request, pk):
    """Download CV as text file"""
    cv = get_object_or_404(CVDocument, pk=pk, user=request.user)
    
    response = HttpResponse(cv.generated_cv_content, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="CV_{cv.full_name}.txt"'
    
    return response