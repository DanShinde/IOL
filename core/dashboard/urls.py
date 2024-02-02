from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from . import views


urlpatterns = [
#dashboard 
    path('', views.home, name = 'dash-home'),
]