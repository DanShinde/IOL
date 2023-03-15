from rest_framework import serializers
from .models import Signals, Module

class SignalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Signals
        fields = '__all__'


class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = '__all__'