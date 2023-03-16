from io import BytesIO
import json
import subprocess
import git
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
import pandas as pd
from rest_framework import generics
from rest_framework.views import APIView
from django.views.generic import TemplateView, CreateView
import xlsxwriter
from rest_framework.response import Response
from .serializers import SignalSerializer, ModuleSerializer
from .forms import ProjectForm
from .models import Project, Module, Signals, IOList
from django.core import serializers
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required,permission_required
from django.contrib.auth import login, logout, authenticate
from django.urls import reverse_lazy
from .forms import RegisterForm, ModuleForm
from django.contrib.auth.mixins import LoginRequiredMixin



@csrf_exempt
def git_update(request):
    if request.method != "POST":
        return HttpResponse("Couldn't update the code on PythonAnywhere")
    '''
        pass the path of the diectory where your project will be 
        stored on PythonAnywhere in the git.Repo() as parameter.
        Here the name of my directory is "test.pythonanywhere.com"
        '''
    repo = git.Repo('/home/iol/IOL')
    origin = repo.remotes.origin
    origin.pull()
    return HttpResponse("Updated code on PythonAnywhere")

class SignUpView(CreateView):
    form_class = RegisterForm
    success_url = reverse_lazy("login")
    template_name = "signup.html"



@login_required(login_url="/login")
def create_project(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save()
            return redirect('project_list') 
    else:
        form = ProjectForm()
    return render(request, 'create_project.html', {'form': form})

@login_required(login_url="/login")
def project_list(request):
    projects = Project.objects.all()
    return render(request, 'project_list.html', {'projects': projects})

@login_required(login_url="/login")
def project_detail(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    modules = Module.objects.all()
    signals = None
    request.session['project'] = project_id
    io_list = IOList.objects.filter(project = project)
    return render(request, 'project_detail.html', {'project': project, 'modules': modules, 'signals': signals, 'io_list': io_list})


def get_signals_for_module(module):
    signals = Signals.objects.filter(module=module)
    return serializers.serialize('json', signals)

@login_required(login_url="/login")
def get_signals(request, module_id):
    module = get_object_or_404(Module, pk=module_id)
    signals = get_signals_for_module(module)
    return HttpResponse(signals, content_type='application/json')

@login_required(login_url="/login")
def get_filtered_signals(request):
    selected_module = request.GET.get('module')
    signals = Signals.objects.filter(module=selected_module).values()
    return JsonResponse({'signals': list(signals)})

@login_required(login_url="/login")
def add_signals(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method.'})
    data = json.loads(request.body)
    signal_ids = data.get('signals', [])
    module_name = data.get('module_name')
    project_id = request.session.get('project')
    project = get_object_or_404(Project, pk=project_id)
    for signal in signal_ids:
        signalData = Signals.objects.get(id=signal)
        if signalData.signal_type == "DI":
            pre = "Ix_"
        elif signalData.signal_type == "DO":
            pre = "Qx_"
        else:
            pre = "Encoder_"
        module = get_object_or_404(Module, pk=signalData.module)
        entry = IOList(
            project=project,
            name=module_name,
            equipment_code=signalData.equipment_code,
            code=signalData.code,
            tag=pre + module_name + "_" + signalData.code,
            signal_type=signalData.signal_type,
            device_type = signalData.device_type,
            actual_description=f"{signalData.component_description}, {signalData.function_purpose}",
            module =  get_object_or_404(Module, pk=signalData.module)
        )
        entry.save()
    io_list = IOList.objects.filter(project = project)
    data = serializers.serialize('json', io_list)

    return JsonResponse({'success': True, 'data': data})


class SignalListView(LoginRequiredMixin, TemplateView):
    template_name = 'editSignals.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        signals = Signals.objects.all()
        serializer = SignalSerializer(signals, many=True)
        context['signals'] = serializer.data
        return context
  

@login_required(login_url="/login")
@csrf_exempt
def update_signal(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    signal_id = request.POST.get('signal_id')
    print(signal_id)
    equipment_code = request.POST.get('equipment_code')
    code = request.POST.get('code')
    component_description = request.POST.get('component_description')
    function_purpose = request.POST.get('function_purpose')
    device_type = request.POST.get('device_type')
    signal_type = request.POST.get('signal_type')
    remarks = request.POST.get('remarks')
    segment = request.POST.get('segment')
    initial_state = request.POST.get('initial_state')
    location = request.POST.get('location')
    
    signal = Signals.objects.get(id=signal_id)
    signal.equipment_code = equipment_code
    signal.code = code
    signal.component_description = component_description
    signal.function_purpose = function_purpose
    signal.device_type = device_type
    signal.signal_type = signal_type
    signal.remarks = remarks
    signal.segment = segment
    signal.initial_state = initial_state
    signal.location = location
    signal.save()

    return JsonResponse({'success': True})

#View to update signals list
@login_required(login_url="/login")
@csrf_exempt
def update(request):
    sig_id= request.POST.get('id','')
    name= request.POST.get('name','')
    value= request.POST.get('value','')
    print(f'id- {sig_id}, name - {name}, value - {value}')
    signal = Signals.objects.get(id=sig_id)
    if name=="code":
        signal.code = value
    elif name == "equipment_code":
        signal.equipment_code = value
    elif name== "component_description": 
        signal.component_description = value
    elif name== "function_purpose":
        signal.function_purpose = value
    elif name== "device_type":
        signal.device_type = value
    elif name== "signal_type":
        signal.signal_type = value
    elif name== "remarks":
        signal.remarks = value
    elif name== "segment":
        signal.segment = value
    elif name== "initial_state":
        signal.initial_state = value
    elif name== "location":
        signal.location = value
    
    signal.save()
    signal = Signals.objects.get(id=sig_id)
    print(signal)
    return JsonResponse({"success":"Updated"})


@login_required(login_url="/login")
def export_to_excel(request):
    project_id = request.session.get('project')
    project = get_object_or_404(Project, id=project_id)
    iolist = IOList.objects.filter(project_id=project_id).order_by('signal_type')
    output = BytesIO()
    # Feed a buffer to workbook
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet(project.name)
    bold = workbook.add_format({'bold': True})
    columns = ["Project", "ModuleName",  "Code", "Tag", "Signal Type","Device Type", "Actual Description"]
    # Fill first row with columns
    row = 0
    for i,elem in enumerate(columns):
        worksheet.write(row, i, elem, bold)
    row += 1
    # Now fill other rows with columns
    for IO in iolist:
        worksheet.write(row, 0, project_id)
        worksheet.write(row, 1, IO.name)
        worksheet.write(row, 2, IO.code)
        worksheet.write(row, 3, IO.tag)
        worksheet.write(row, 4, IO.signal_type)
        worksheet.write(row, 5, IO.actual_description)
        worksheet.write(row, 6, IO.device_type)
        row += 1

    workbook.close()
    output.seek(0)
    response = HttpResponse(output.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    return response

def module_list(request):
    modules = Module.objects.all()
    if request.method == 'POST':
        if 'add_module' in request.POST:
            module_name = request.POST['module_name']
            module = Module.objects.create(module=module_name)
            return redirect('module_list')
        elif 'delete_module' in request.POST:
            module_id = request.POST['module_id']
            Module.objects.filter(id=module_id).delete()
            return redirect('module_list')
    return render(request, 'module_list.html', {'modules': modules})

def modules(request):
    if request.method =="POST":
        form = ModuleForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                return redirect('/show')
            except:
                pass
    else:
        form = ModuleForm()
    return render(request, 'cluster_list.html', {'form' : form})

"""
def show_module(request):
    modules = Module.objects.all()
    return render(request, 'cluster_list.html', {'modules' :modules})

def edit_module(request, id):
    module = Module.objects.get(id = id)
    return render(request, 'cluster_list.html', {'module' :module})


def update_module(request, id):
    module = Module.objects.get(id=id)
    form = ModuleForm(request.POST, instance= module)
    if form.is_valid():
        form.save()
        return redirect('/show_module')
    
    return render(request, 'edit_module.html', {'module' :module})


def destroy(request, id):
    module = Module.objects.get(id=id)
    module.delete()
    return redirect('/show_module')
    
"""
def module_destroy(request, id):
    module = Module.objects.get(id=id)
    module.delete()
    return redirect('/module_list')

class ModuleListView(LoginRequiredMixin, TemplateView):
    template_name = 'update_module.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        modules = Module.objects.all()
        serializer = ModuleSerializer(modules, many = True)
        context["modules"] = serializer.data
        return context


@login_required(login_url="/login")
@csrf_exempt
def update_module(request):
    sig_id= request.POST.get('id','')
    name= request.POST.get('name','')
    value= request.POST.get('value','')
    print(f'id- {sig_id}, name - {name}, value - {value}')
    module = Module.objects.get(id=sig_id)
    module.module = value

    module.save()
    module = Module.objects.get(id=sig_id)
    print(module)
    return JsonResponse({"success":"Updated"})
