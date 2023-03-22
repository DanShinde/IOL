from datetime import datetime
from io import BytesIO
import json
import math
import subprocess
from django.forms import inlineformset_factory
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views import View
import pandas as pd

from sorting.utils import get_max_order
from .utils import get_max_cluster_number
from django.contrib import messages
from django.db.models import Q, OuterRef, Subquery
from django.views.generic import TemplateView
import xlsxwriter
from django.template.loader import render_to_string
from django.template import loader
from rest_framework.response import Response
from .serializers import SignalSerializer, ModuleSerializer
from .forms import ProjectForm, SignalsForm, IOListForm, ClusterForm
from .models import Project, Module, Signals, IOList
from django.core import serializers
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required,permission_required
from django.contrib.auth import login, logout, authenticate
from django.http import QueryDict
from django.contrib.auth.mixins import LoginRequiredMixin


def home(request):
    return redirect('project_list') 




@login_required(login_url="/accounts/login")
def create_project(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.created_by = request.user.get_full_name()
            project.updated_at = datetime.now()
            project.save()
            return redirect('project_list') 
    else:
        form = ProjectForm()
    return render(request, 'projects/create_project.html', {'form': form})


# To view list of projects
@login_required(login_url="/accounts/login")
def project_list(request):
    projects = Project.objects.all()
    return render(request, 'projects/project_list.html', {'projects': projects})

# Window to add signals to project
@login_required(login_url="/accounts/login")
def project_detail(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    modules = Module.objects.all()
    signals = None
    request.session['project'] = project_id
    io_list = IOList.objects.filter(project = project).order_by('-id')
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
    panel_number = data.get('panel_number')
    print(panel_number)
    
    project_id = request.session.get('project')
    project = get_object_or_404(Project, pk=project_id)
    project.updated_at = datetime.now()
    project.save()
    cluster_number = get_max_cluster_number(project)
    print(f'Max cluster number is {cluster_number}.')
    for signal in signal_ids:
        signalData = Signals.objects.get(id=signal)
        if signalData.signal_type == "DI":
            pre = "Ix_"
        elif signalData.signal_type == "DO":
            pre = "Qx_"
        else:
            pre = "Encoder_"
        order = get_max_order(project)
        entry = IOList(
            project=project,
            name=module_name,
            equipment_code=signalData.equipment_code,
            code=signalData.code,
            tag=pre + module_name + "_" + signalData.code,
            signal_type=signalData.signal_type,
            device_type = signalData.device_type,
            actual_description=f"{signalData.component_description}, {signalData.function_purpose}",
            Cluster =  signalData.module,
            panel_number = panel_number,
            created_by = request.user.get_full_name(),
            order = order,
            location = signalData.location,
            cluster_number = cluster_number,
        )
        entry.save()
        
    io_list = IOList.objects.filter(project = project).order_by('-id')
    # print(io_list)
    data = serializers.serialize('json', io_list)

    return JsonResponse({'success': True, 'data': data})

def add_spares(worksheet,row, project, IO, count,I_Pointer, Q_Pointer):
    worksheet.write(row, 0, row-1)
    worksheet.write(row, 1, "Spare")
    worksheet.write(row, 2, "Spare")
    if IO.signal_type == "DI":
        worksheet.write(row, 3, f'Ix_Spare_Spare_{count}')
    elif IO.signal_type == "DO":
        worksheet.write(row, 3, f'Qx_Spare_Spare_{count}')
    worksheet.write(row, 4, IO.signal_type)
    worksheet.write(row, 5, "Spare_Signal")
    if IO.signal_type == "DI":
        # print(f'I_Pointer {I_Pointer}.')
        x = f"I{str(math.floor((I_Pointer - 1) / 8))}.{str((I_Pointer - 1) % 8)}"
        # print(x)
    elif IO.signal_type == "DO":
        x = f"Q{str(math.floor((Q_Pointer - 1) / 8))}.{str((Q_Pointer - 1) % 8)}"
        # print(x)
    worksheet.write(row, 6, x)
    worksheet.write(row, 7, "Spare Signal")
    worksheet.write(row, 8, IO.panel_number)
    worksheet.write(row, 9, "CP")
    return worksheet, I_Pointer, Q_Pointer

#function to write indivisual sheets while exporting
def write_sheet(panel,workbook, project, iolist, I_Pointer, Q_Pointer):
    worksheet = workbook.add_worksheet(panel)
    bold = workbook.add_format({'bold': True})
    columns = ["Project", "ModuleName",  "Code", "Tag", "Signal Type","Device Type","I/O Address","Actual Description","Panel Number","Location"]
    # Fill first row with columns
    row = 0
    for i,elem in enumerate(columns):
        worksheet.write(row, i, elem, bold)
    row += 1
    # Now fill other rows with columns
    i = 0
    q = 0
    # Writing DIs to file
    for IO in iolist:
        if IO.signal_type == "DI":
            worksheet.write(row, 0, row-1)
            worksheet.write(row, 1, IO.name)
            worksheet.write(row, 2, IO.code)
            worksheet.write(row, 3, IO.tag)
            worksheet.write(row, 4, IO.signal_type)
            worksheet.write(row, 5, IO.device_type)
            if IO.signal_type == "DI":
                x = f"I{str(math.floor((I_Pointer - 1) / 8))}.{str((I_Pointer - 1) % 8)}"
                I_Pointer+= 1
            elif IO.signal_type == "DO":
                x = f"Q{str(math.floor((Q_Pointer - 1) / 8))}.{str((Q_Pointer - 1) % 8)}"
                Q_Pointer+= 1
            IO.io_address =  x
            IO.save()
            worksheet.write(row, 6, IO.io_address)
            worksheet.write(row, 7, IO.actual_description)
            worksheet.write(row, 8, IO.panel_number)
            worksheet.write(row, 9, IO.location)
            row += 1
            i+= 1
            q+= 1
            IOOut = IO
    # print(IOOut.signal_type)
    print(F'Panel number {panel} of I_Pointer count {I_Pointer}.')
    #Adding Input spares
    for i in range(0,16- ( ((I_Pointer-1)%16))):
        count = i+1
        worksheet, I_Pointer, Q_Pointer = add_spares(worksheet,row,project,IOOut, count, I_Pointer, Q_Pointer)
        I_Pointer+= 1
        row += 1
        # print(I_Pointer)

    #Writing DOs to file
    for IO in iolist:
        if IO.signal_type == "DO":
            worksheet.write(row, 0, row-1)
            worksheet.write(row, 1, IO.name)
            worksheet.write(row, 2, IO.code)
            worksheet.write(row, 3, IO.tag)
            worksheet.write(row, 4, IO.signal_type)
            worksheet.write(row, 5, IO.device_type)
            if IO.signal_type == "DI":
                x = f"I{str(math.floor((I_Pointer - 1) / 8))}.{str((I_Pointer - 1) % 8)}"
                I_Pointer+= 1
            elif IO.signal_type == "DO":
                x = f"Q{str(math.floor((Q_Pointer - 1) / 8))}.{str((Q_Pointer - 1) % 8)}"
                Q_Pointer+= 1
            IO.io_address =  x
            IO.save()
            worksheet.write(row, 6, IO.io_address)
            worksheet.write(row, 7, IO.actual_description)
            worksheet.write(row, 8, IO.panel_number)
            worksheet.write(row, 9, IO.location)
            row += 1
            i+= 1
            q+= 1
            IOOut = IO
    print(F'Panel number {panel} of I_Pointer count {Q_Pointer}.')
    #Adding Output spares
    for i in range(0,16- ( ((Q_Pointer-1)%16))):
        count = i+1
        worksheet, I_Pointer, Q_Pointer = add_spares(worksheet,row,project,IOOut, count, I_Pointer, Q_Pointer)
        row += 1
        Q_Pointer+= 1
        # print(Q_Pointer)
    print(F'Panel number {panel} of count {I_Pointer}, {Q_Pointer}.')
    return workbook, I_Pointer, Q_Pointer


#EXporting IO List to Excel file
@login_required(login_url="/accounts/login")
def export_to_excel(request):
    project_id = request.session.get('project')
    project = get_object_or_404(Project, id=project_id)
    iolist = IOList.objects.filter(project_id=project_id).order_by('signal_type', 'location','order')
    panels = [i.panel_number for i in iolist]
    panels =[*set(panels)]
    print(panels)
    I_Pointer = 1
    Q_Pointer = 1
    output = BytesIO()
    # Feed a buffer to workbook
    workbook = xlsxwriter.Workbook(output)
    
    while None in panels:
        # removing None from list using remove method
        panels.remove(None)
    
    for panel in sorted(panels):
        print(panel)
        panelIO = iolist.filter(panel_number=panel)
        workbook, I_Pointer, Q_Pointer = write_sheet(panel, workbook, project, panelIO, I_Pointer, Q_Pointer )

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
    if request.user.groups.filter(name='Managers').exists():
        module = Module.objects.get(id=id)
        module.delete()
        return redirect('/module_list')
    else :
        return HttpResponse("User does not have permissions to delete")

# form to add new module
@login_required(login_url="/accounts/login")
def create_module(request):
    if request.method == 'POST':
        form = ClusterForm(request.POST)
        if form.is_valid():
            module = form.save(commit=False)
            module.created_by = request.user.get_full_name()
            module.save()
            request.session['module'] = module.id
            return redirect('module_list') 
    else:
        form = ClusterForm()
    return render(request, 'update_data/form_module.html', {'form': form})



# For Editing Signal in CLusters/ Modules
def edit_module(request, module_id):
    request.session['module'] = module_id
    return redirect('/signals')
 
def iolist_project(request, project_id):
    request.session['project'] = project_id
    return redirect(f'/iolist/{project_id}/get')

class IolistView(View):

    context = {'segment': 'iolist'}


    def get(self, request, *args, **kwargs):
        project_id = kwargs.get('pk')
        iolists =IOList.objects.filter(project_id=project_id)
        project = get_object_or_404(Project, pk=project_id)
        self.context['project'] = project
        self.context['io_list'] = iolists
        return render(request, 'projects/iolist.html', self.context)
    

    def delete(self, request, *args, **kwargs):
        # sourcery skip: class-extract-method
        iolist = get_object_or_404(IOList, id=kwargs.get('pk'))
        project= iolist.project
        iolist.delete()
        redirect_url = reverse('iolist')
        
        response = {'valid': 'success', 'message': 'Item deleted successfully', 'redirect_url': redirect_url}
        return redirect((f'/iolist/{project.id}/get'))
    

    def edit(self, request, *args, **kwargs):
        iolist = get_object_or_404(IOList, id=kwargs.get('pk'))
        if request.method == 'POST':
            form = IOListForm(request.POST, instance=iolist)
            print("It's Post")
            if form.is_valid():
                form.save()
                print("It's Save")
                messages.success(request, 'Item updated successfully')
                redirect_url = reverse('iolist')
                response = {'valid': 'success', 'message': 'Item updated successfully', 'redirect_url': redirect_url}
                return redirect('iolist')
            else:
                print(form.errors)
        else:
            form = IOListForm(instance=iolist)
        project_id = request.session.get('project')
        project = get_object_or_404(Project, pk=project_id)
        context = {
            'form': form,
            'iolist': iolist,
            'action': 'edit',
            'project': project,
        }
        return render(request, 'projects/edit_iolist.html', context)

    def dispatch(self, request, *args, **kwargs):
        if kwargs.get('action') == 'get':
            return self.get(request, *args, **kwargs)
        elif kwargs.get('action') == 'delete':
            return self.delete(request, *args, **kwargs)
        elif kwargs.get('action') == 'edit':
            return self.edit(request, *args, **kwargs)
        else:
            return super().dispatch(request, *args, **kwargs)



class ClusterView(View):

    context = {'signal_list': 'signal_list'}


    def get(self, request, pk=None, action=None):
        module_id = request.session.get('module')
        signal_list =Signals.objects.filter(module_id=module_id)
        module = get_object_or_404(Module, pk=module_id)
        self.context['module'] = module
        self.context['signal_list'] = signal_list
        return render(request, 'update_data/cluster_signals.html', self.context)
    

    def delete(self, request, *args, **kwargs):
        # sourcery skip: class-extract-method
        if request.user.groups.filter(name='Managers').exists():
            signal_list = get_object_or_404(Signals, id=kwargs.get('pk'))
            signal_list.delete()
            redirect_url = reverse('signals')
            response = {'valid': 'success', 'message': 'Item deleted successfully', 'redirect_url': redirect_url}
            print("Deleted Cluster")
            return redirect('signals')
        else:
            return HttpResponse("User does not have permissions to delete")
    

    def add(self, request, *args, **kwargs):  # sourcery skip: extract-method
        if request.method == 'POST':
            form = SignalsForm(request.POST)
            if form.is_valid():
                signal = form.save(commit=False)
                signal.created_by = request.user.get_full_name()
                module_id = request.session.get('module')
                module = get_object_or_404(Module, id= module_id)
                signal.module = module
                signal.save()
                module.updated_at = datetime.now()
                module.save()
                return redirect('signals')
        else:
            form = SignalsForm()
        return render(request, 'update_data/edit_signal.html', {'form': form})

    

    def edit(self, request, *args, **kwargs):
        signal = get_object_or_404(Signals, id=kwargs.get('pk'))
        if request.method == 'POST':
            form = SignalsForm(request.POST, instance=signal)
            print("It's Post")
            if form.is_valid():
                form.save()
                print("It's Save")
                messages.success(request, 'Item updated successfully')
                redirect_url = reverse('signals')
                response = {'valid': 'success', 'message': 'Item updated successfully', 'redirect_url': redirect_url}
                return redirect('signals')
            else:
                print(form.errors)
        else:
            form = SignalsForm(instance=signal)
        module_id = request.session.get('module')
        module = get_object_or_404(Module, pk=module_id)
        context = {
            'form': form,
            'signals': signal,
            'action': 'edit',
            'module': module,
        }
        return render(request, 'update_data/edit_signal.html', context)

    def dispatch(self, request, *args, **kwargs):
        if kwargs.get('action') is None:
            return self.get(request, *args, **kwargs)
        elif kwargs.get('action') == 'delete':
            return self.delete(request, *args, **kwargs)
        elif kwargs.get('action') == 'edit':
            return self.edit(request, *args, **kwargs)
        elif kwargs.get('action') == 'add':
            return self.add(request, *args, **kwargs)
        else:
            return super().dispatch(request, *args, **kwargs)


