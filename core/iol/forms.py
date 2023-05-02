from django import forms
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from .models import Project, Module, Signals, IOList
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.forms.models import inlineformset_factory, BaseInlineFormSet

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description', 'segment', 'is_Murr', 'PLC', 'panel_numbers']
        exclude = ['created_by', 'created_at', 'updated_at']


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name','username','email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True




class SignalsForm(forms.ModelForm):
    class Meta:
        model = Signals
        fields = '__all__'
        exclude = ['created_by', 'created_at', 'updated_at', 'module']
        widgets = {
            'equipment_code': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'component_description': forms.Textarea(attrs={'class': 'form-control'}),
            'function_purpose': forms.Textarea(attrs={'class': 'form-control'}),
            'device_type': forms.TextInput(attrs={'class': 'form-control'}),
            'signal_type': forms.Select(attrs={'class': 'form-control'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control'}),
            'segment': forms.TextInput(attrs={'class': 'form-control'}),
            'initial_state': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'location': forms.Select(attrs={'class': 'form-control'}),
            'module': forms.Select(attrs={'class': 'form-control'}),
            'Demo_3d_Property': forms.TextInput(attrs={'class': 'form-control'}),
            
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.groups.filter(name='Emulation').exists():
            # Disable fields that are not allowed for emulation group
            self.fields['equipment_code'].widget.attrs['readonly'] = True
            self.fields['code'].widget.attrs['readonly'] = True
            self.fields['component_description'].widget.attrs['readonly'] = True
            self.fields['function_purpose'].widget.attrs['readonly'] = True
            self.fields['device_type'].widget.attrs['readonly'] = True
            self.fields['signal_type'].widget.attrs['style'] = 'display: none;'
            self.fields['segment'].widget.attrs['readonly'] = True
            self.fields['remarks'].widget.attrs['readonly'] = True
            self.fields['initial_state'].widget.attrs['style'] = 'display: none;'
            self.fields['location'].widget.attrs['style'] = 'display: none;'
            # self.fields['module'].widget.attrs['readonly'] = True
            
            

class IOListForm(forms.ModelForm):
    class Meta:
        model = IOList
        exclude = ['created_by', 'created_at', 'updated_at', 'io_address','channel', 'cluster_number', 'order']
        widgets = {
            'project': forms.TextInput(attrs={'class': 'form-control', 'readonly' : 'readonly'}),
        }

class ClusterForm(forms.ModelForm):
    class Meta:
        model = Module
        exclude = ['created_by', 'created_at', 'updated_at']
        widgets = {
            'project': forms.TextInput(attrs={'class': 'form-control', 'readonly' : 'readonly'}),
        }

