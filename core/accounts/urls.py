from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from . import views


urlpatterns = [
#Login 
    path('login/', LoginView.as_view(template_name='base/login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path("sign-up/", views.SignUpView.as_view(), name="signup"),
    path('git_update/', views.git_update, name = 'git-update'),
]