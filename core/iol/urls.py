from django.urls import path, re_path
from . import views
from .views import ModuleListView, IolistView
from django.contrib.auth.decorators import login_required

urlpatterns = [

    ###
    path('add_signals/', views.add_signals, name= 'add_signals'),
    path('projects/create/', views.create_project, name='create_project'),
    path('project_list', views.project_list, name='project_list'),
    path('', views.home, name='home'),
    path('projects/<int:project_id>/', views.project_detail, name='project_detail'),
    path('get_signals/<int:module_id>/', views.get_signals_for_module, name='get_signals'),
    path('get_filtered_signals/', views.get_filtered_signals, name='get_filtered_signals'),
    path('toexcel/', views.export_to_excel, name= "to-excel"),



    #To manage modules & signals

    path('module_list/', ModuleListView.as_view(), name='module_list'),
    path('module_list/<int:id>/delete/', views.module_destroy, name='module_delete'),
    path('module_edit/<int:id>/', views.edit_module, name = 'module_edit'),
    path('module_edit/<int:id>/delete/', views.signal_delete, name='signal_delete'),

    # re_path(r'^signals/(?:(?P<pk>\d+)/)?(?:(?P<action>\w+)/)?', views.SignalsView.as_view(), name='signals'),

    re_path(r'^iolist/(?:(?P<pk>\d+)/)?(?:(?P<action>\w+)/)?',  login_required(views.IolistView.as_view()), name='iolist'),
]



