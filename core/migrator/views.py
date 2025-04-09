from django.shortcuts import render

# Create your views here.
from rest_framework.viewsets import ReadOnlyModelViewSet
from iol.models import Project, Module, Signals, IOList, ProjectReport
from iol.serializers import ProjectSerializer, ModuleSerializer, SignalSerializer, IOListSerializer, ProjectReportSerializer



class ProjectViewSet(ReadOnlyModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

class ModuleViewSet(ReadOnlyModelViewSet):
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer

class SignalViewSet(ReadOnlyModelViewSet):
    queryset = Signals.objects.all()
    serializer_class = SignalSerializer 

class IOListViewSet(ReadOnlyModelViewSet):
    queryset = IOList.objects.all()
    serializer_class = IOListSerializer

class ProjectReportViewSet(ReadOnlyModelViewSet):
    queryset = ProjectReport.objects.all()
    serializer_class = ProjectReportSerializer