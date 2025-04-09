from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, ModuleViewSet, SignalViewSet, IOListViewSet, ProjectReportViewSet
from django.urls import path, include

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='m-project')
router.register(r'modules', ModuleViewSet, basename='m-module')
router.register(r'signals', SignalViewSet, basename='m-signal')
router.register(r'iolists', IOListViewSet, basename='m-iolist')
router.register(r'projectreports', ProjectReportViewSet, basename='m-projectreport')

urlpatterns = [
    path('', include(router.urls)),
]