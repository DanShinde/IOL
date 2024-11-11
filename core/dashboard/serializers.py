
from rest_framework import serializers
from iol.models import Project, Module, IOList, Signals, ProjectReport

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'

class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = '__all__'

class IOListSerializer(serializers.ModelSerializer):
    project_id = serializers.PrimaryKeyRelatedField(queryset=Project.objects.all(), source='project', write_only=True)
    class Meta:
        model = IOList
        fields = '__all__'

class SignalsSerializer(serializers.ModelSerializer):
    module_id = serializers.PrimaryKeyRelatedField(queryset=Module.objects.all(), source='module', write_only=True)
    class Meta:
        model = Signals
        fields = '__all__'


class ProjectReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectReport
        fields = '__all__'
		
		
		
		
		