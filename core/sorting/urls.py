from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from . import views


urlpatterns = [
#Login 

]

htmx_views = [
    path('<int:project_id>/', views.IOListView.as_view(template_name='sorting/sorting.html'), name='sorting'),
    path('tag-delete/<int:pk>/', views.delete_tag, name='tag-delete'),
    path('sort_IO/', views.sort_IO, name= "sort_IO"),
    path('cluster_number_update/<int:pk>/<str:action>', views.cluster_number_update, name= "cluster_number_update"),
    path('module_position_update/<int:pk>/<str:action>', views.module_position_update, name= "module_position_update"),
    path('order_update/<int:pk>/<str:action>', views.order_update, name= "order_update"),
    path('delete_signal/<int:pk>/', views.delete_in_Reorder, name='delete-signal-reorder'),
    path('grouping/<int:project_id>/<int:page_number>', views.group_view, name='grouping'),
    path('groupingnext/', views.ngroup_view, name='groupingnext'),
    path('groupingprev/', views.pgroup_view, name='groupingprev'),
    path('update-clustern/', views.update_clustern, name='update_data'),
]

urlpatterns += htmx_views

