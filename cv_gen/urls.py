from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.CVDashboardView.as_view(), name='cv_dashboard'),
    
    # Create CV flow
    path('create/', views.CVCreateView.as_view(), name='cv_create'),
    path('<int:pk>/work-experience/', views.AddWorkExperienceView.as_view(), name='cv_work_experience'),
    path('<int:pk>/education/', views.AddEducationView.as_view(), name='cv_add_education'),
    path('<int:pk>/skills/', views.AddSkillsView.as_view(), name='cv_add_skills'),
    path('<int:pk>/generate/', views.GenerateCVView.as_view(), name='cv_generate'),
    path('<int:pk>/preview/', views.CVPreviewView.as_view(), name='cv_preview'),
    
    # Edit and Delete
    path('<int:cv_id>/work-experience/<int:job_id>/edit/', views.EditWorkExperienceView.as_view(), name='edit_work_experience'),
    path('<int:cv_id>/work-experience/<int:job_id>/delete/', views.delete_work_experience, name='delete_work_experience'),
    path('<int:cv_id>/education/<int:edu_id>/delete/', views.delete_education, name='delete_education'),
    path('<int:cv_id>/skill/<int:skill_id>/delete/', views.delete_skill, name='delete_skill'),
    
    # Download
    path('<int:pk>/download/', views.download_cv_txt, name='download_cv_txt'),
]