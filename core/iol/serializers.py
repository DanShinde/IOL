from rest_framework import serializers
from .models import Signals, Module, Project, ProjectReport, IOList

class SignalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Signals
        fields = '__all__'


class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = '__all__'


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'

class SignalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Signals
        fields = '__all__'


class ProjectReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectReport
        fields = '__all__'

# Serializer for IOList Model
class IOListSerializer(serializers.ModelSerializer):
    class Meta:
        model = IOList
        fields = '__all__'  # Serialize all fields
