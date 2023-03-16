
from django.urls import path, include
from . import views
from rest_framework import routers
from .views import SignalListView, ModuleListView
from django.contrib.auth.views import LoginView


urlpatterns = [
    #Login 
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
    path("sign-up/", views.SignUpView.as_view(), name="signup"),
    path('git_update/', views.git_update, name = 'git-update'),
    ###
    path('add_signals/', views.add_signals, name= 'add_signals'),
    path('projects/create/', views.create_project, name='create_project'),
    path('', views.project_list, name='project_list'),
    path('projects/<int:project_id>/', views.project_detail, name='project_detail'),
    path('get_signals/<int:module_id>/', views.get_signals_for_module, name='get_signals'),
    path('get_filtered_signals/', views.get_filtered_signals, name='get_filtered_signals'),
    path('update_signal/', views.update_signal, name='update_signal'),
    path('signals/', SignalListView.as_view(), name='signals-list'),
    path('signals/update/', views.update, name = 'update'),
    path('toexcel/', views.export_to_excel, name= "to-excel"),

    #To manage modules & signals
    #path('update_module/', views.update_module, name='update_module'),
    path('module_list/', ModuleListView.as_view(), name='module_list'),
    path('module_list/edit/', views.update_module, name = 'module_edit'),
    path('module_list/<int:id>/delete/', views.module_destroy, name='module_delete'),
]



