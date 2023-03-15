from django import forms
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from .models import Project, Module, Signals
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.forms.models import inlineformset_factory, BaseInlineFormSet


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description']

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name','username','email', 'password1', 'password2']


class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = "__all__"
