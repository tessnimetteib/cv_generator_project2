"""
CV Analyzer URL Configuration
"""

from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from cv_gen.views import home, signup

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('cv/', include('cv_gen.urls')),
    
    # Authentication URLs
    path('accounts/login/', auth_views.LoginView.as_view(template_name='cv_gen/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('accounts/signup/', signup, name='signup'),
]