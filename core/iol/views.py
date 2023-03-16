from io import BytesIO
import json
import subprocess
from django.forms import inlineformset_factory
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
import pandas as pd
from django.views.generic import TemplateView
import xlsxwriter
from rest_framework.response import Response
from .serializers import SignalSerializer, ModuleSerializer
from .forms import ProjectForm, SignalsForm, SignalsFormSet
from .models import Project, Module, Signals, IOList
from django.core import serializers
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required,permission_required
from django.contrib.auth import login, logout, authenticate

from .forms import ModuleForm
from django.contrib.auth.mixins import LoginRequiredMixin


def home(request):
    return redirect('project_list') 


@login_required(login_url="/accounts/login")
def create_project(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save()
            return redirect('project_list') 
    else:
        form = ProjectForm()
    return render(request, 'projects/create_project.html', {'form': form})


@login_required(login_url="/accounts/login")
def project_list(request):
    projects = Project.objects.all()
    return render(request, 'projects/project_list.html', {'projects': projects})

@login_required(login_url="/accounts/login")
def project_detail(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    modules = Module.objects.all()
    signals = None
    request.session['project'] = project_id
    io_list = IOList.objects.filter(project = project)
    return render(request, 'projects/project_detail.html', {'project': project, 'modules': modules, 'signals': signals, 'io_list': io_list})


#Get signals of selected Conveyor Cluster/ Module
def get_signals_for_module(module):
    signals = Signals.objects.filter(module=module)
    return serializers.serialize('json', signals)

# Pass signals to request
@login_required(login_url="/accounts/login")
def get_signals(request, module_id):
    module = get_object_or_404(Module, pk=module_id)
    signals = get_signals_for_module(module)
    return HttpResponse(signals, content_type='application/json')


@login_required(login_url="/accounts/login")
def get_filtered_signals(request):
    selected_module = request.GET.get('module')
    signals = Signals.objects.filter(module=selected_module).values()
    return JsonResponse({'signals': list(signals)})


#Add Signals to IO List
@login_required(login_url="/accounts/login")
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

        entry = IOList(
            project=project,
            name=module_name,
            equipment_code=signalData.equipment_code,
            code=signalData.code,
            tag=pre + module_name + "_" + signalData.code,
            signal_type=signalData.signal_type,
            device_type = signalData.device_type,
            actual_description=f"{signalData.component_description}, {signalData.function_purpose}",
            module =  signalData.module
        )
        entry.save()
    io_list = IOList.objects.filter(project = project)
    data = serializers.serialize('json', io_list)

    return JsonResponse({'success': True, 'data': data})


#EXporting IO List to Excel file
@login_required(login_url="/accounts/login")
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
        worksheet.write(row, 6, IO.device_type)
        worksheet.write(row, 5, IO.actual_description)
        row += 1

    workbook.close()
    output.seek(0)
    response = HttpResponse(output.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    return response

#Get list of Clusters/ Modules
class ModuleListView(LoginRequiredMixin, TemplateView):
    template_name = 'update_data/update_module.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        modules = Module.objects.all()
        serializer = ModuleSerializer(modules, many = True)
        context["modules"] = serializer.data
        return context


#Delete Cluster / Module
def module_destroy(request, id):
    module = Module.objects.get(id=id)
    module.delete()
    return redirect('/module_list')



# @login_required(login_url="/accounts/login")
# @csrf_exempt
# def update_module(request):
#     sig_id= request.POST.get('id','')
#     name= request.POST.get('name','')
#     value= request.POST.get('value','')
#     print(f'id- {sig_id}, name - {name}, value - {value}')
#     module = Module.objects.get(id=sig_id)
#     module.module = value

#     module.save()
#     module = Module.objects.get(id=sig_id)
#     print(module)
#     return JsonResponse({"success":"Updated"})



def edit_module(request, id):
    module = get_object_or_404(Module, pk=id)
    signals = Signals.objects.filter(module=module)
    return render(request, 'edit_module.html', {'signals': signals})

def signal_delete(request, id):
    signal = Signals.objects.get(id=id)
    signal.delete()
    return redirect('/module_edit')
