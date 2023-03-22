from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from . import views


urlpatterns = [
#Login 

]

htmx_views = [
    path('<int:project_id>', views.IOListView.as_view(template_name='sorting/sorting.html'), name='sorting'),
    path('tag-delete/<int:pk>/', views.delete_tag, name='tag-delete'),
    path('sort_IO/', views.sort_IO, name= "sort_IO"),
]

urlpatterns += htmx_views