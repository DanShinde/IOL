from datetime import datetime
from io import BytesIO
import json
import math
import subprocess
from django.forms import inlineformset_factory
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden, HttpResponseNotFound, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views import View
import pandas as pd
from django.utils.decorators import method_decorator
from sorting.utils import get_max_order
from .utils import get_max_cluster_number, add_Murr_spares
from django.contrib import messages
from django.db.models import Q, OuterRef, Subquery, Count
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
    user_groups = request.user.groups.values_list('name', flat=True)
    projects = Project.objects.filter(segment__in=user_groups).distinct()
    return render(request, 'projects/project_list.html', {'projects': projects})

    # projects = Project.objects.all()
    # return render(request, 'projects/project_list.html', {'projects': projects})

# Window to add signals to project
@login_required(login_url="/accounts/login")
def project_detail(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    segment = project.segment
    if not request.user.groups.filter(name= segment).exists():
        print("Not in group")
        return HttpResponseForbidden()
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
    project_id = request.session.get('project')
    project = get_object_or_404(Project, pk=project_id)
    project.updated_at = datetime.now()
    project.save()
    cluster_number = get_max_cluster_number(project)
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
    if project.is_Murr:
        io_list_to_order = IOList.objects.filter(project = project).order_by('cluster_number', 'order')
    else:
        io_list_to_order = IOList.objects.filter(project = project).order_by('signal_type', 'location')
    temp_Add = 0
    for index, signal in enumerate(io_list_to_order, start=1):
        signal.order = (((index-1)//14)*2) + index if project.is_Murr else index
        # print(f'Order is {signal.order}')
        signal.module_position =1+ (index-1)//14 if project.is_Murr else 1+ (index-1)//16
        # signal.save()

    
    IOList.objects.bulk_update(io_list_to_order, ['order'])
    IOList.objects.bulk_update(io_list_to_order, ['module_position'])
    io_list = IOList.objects.filter(project = project).order_by('-id')
    data = render_to_string('projects/iolist_in_add.html', {'io_list': io_list})
    return JsonResponse({'success': True, 'data': data})

def add_spares(worksheet,row, project, IO, count,I_Pointer, Q_Pointer, panel_n, signal_type):
    channel = (row - 1) % 16 + 1
    worksheet.write(row, 0, row)
    worksheet.write(row, 1, "Spare")
    worksheet.write(row, 2, "Spare")
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    worksheet.write(row, 4, signal_type)
    worksheet.write(row, 5, "Spare_Signal")
    if project.is_Murr:
        if project.PLC == "Allen Bradley":
            x = f"RACK{letters[panel_n]}:{math.floor((I_Pointer - 1) / 8) + 1}:I.{(I_Pointer - 1) % 8 + 1}"
        else:
            x = f"I{str(math.floor((I_Pointer - 1) / 8))}.{str((I_Pointer - 1) % 8)}"
        worksheet.write(row, 3, f'Ix_Spare_Spare_{count}')
        I_Pointer+= 1
    else:
        if signal_type == "DI":
            worksheet.write(row, 3, f'Ix_Spare_Spare_{count}')
        elif signal_type == "DO":
            worksheet.write(row, 3, f'Qx_Spare_Spare_{count}')
        if signal_type == "DI":
            # print(f'I_Pointer {I_Pointer}.')
            letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            if project.PLC == "Allen Bradley":
                x = f"RACK{letters[panel_n]}:{math.floor((I_Pointer - 1) / 8) + 1}:I.{(I_Pointer - 1) % 8}"
            else:
                x = f"I{str(math.floor((I_Pointer - 1) / 8))}.{str((I_Pointer - 1) % 8)}"
            I_Pointer+= 1
            # print(x)
        elif signal_type == "DO":
            letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            if project.PLC == "Allen Bradley":
                x = f"RACK{letters[panel_n]}:{math.floor((I_Pointer - 1) / 8) + 1}:O.{(I_Pointer - 1) % 8}"
                I_Pointer+= 1
            else:
                x = f"Q{str(math.floor((Q_Pointer - 1) / 8))}.{str((Q_Pointer - 1) % 8)}"
                Q_Pointer+= 1
        # print(x)
    worksheet.write(row, 6, x)
    worksheet.write(row, 7, "Spare Signal")
    worksheet.write(row, 8, channel)
    worksheet.write(row, 9, IO.module_position)
    worksheet.write(row, 10, IO.panel_number)
    worksheet.write(row, 11, "CP")
    if project.is_Murr:
                worksheet.write(row, 12, "X4" if row%2 == 0 else "X2")
                worksheet.write(row, 13, f'X{(row-1 % 16+1) // 2}')
    return worksheet, I_Pointer, Q_Pointer

#function to write indivisual sheets while exporting
def write_sheet(panel,workbook, project, iolist, I_Pointer, Q_Pointer, panel_n):
    worksheet = workbook.add_worksheet(panel)
    bold = workbook.add_format({'bold': True})
    columns = ["Sr.No.", "ModuleName",  "Code", "Tag", "Signal Type","Device Type","I/O Address","Actual Description", 'Channel','Module Position',"Panel Number","Location"]
    if project.is_Murr:
        columns.extend(("Port", "Murr Channel"))
    # Fill first row with columns
    row = 0
    for i,elem in enumerate(columns):
        worksheet.write(row, i, elem, bold)
    row += 1
    # Now fill other rows with columns
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    # Writing DIs to file
    for IO in iolist:
        IOOut = IO
        if IO.signal_type == "DI" or project.is_Murr:
            while project.is_Murr and ((row-1) % 16 )+1 in [15,16]:
                worksheet, I_Pointer = add_Murr_spares(worksheet,row,project,IO,I_Pointer, panel_n)
                row += 1

            # print('Signal Added')
            channel = (row - 1) % 16 + 1
            worksheet.write(row, 0, row)
            worksheet.write(row, 1, IO.name)
            worksheet.write(row, 2, IO.code)
            worksheet.write(row, 3, IO.tag)
            worksheet.write(row, 4, IO.signal_type)
            worksheet.write(row, 5, IO.device_type)
            if (
                (project.is_Murr
                and IO.signal_type == "DI")
                or (not project.is_Murr
                and IO.signal_type == "DI")
            ):
                if project.PLC == "Allen Bradley":
                    x = f"RACK{letters[panel_n]}:{math.floor((I_Pointer - 1) / 8) + 1}:I.{(I_Pointer - 1) % 8 }"
                else:
                    x = f"I{str(math.floor((I_Pointer - 1) / 8))}.{str((I_Pointer - 1) % 8)}"
                I_Pointer+= 1
            elif project.is_Murr and IO.signal_type == "DO":
                if project.PLC == "Allen Bradley":
                    x = f"RACK{letters[panel_n]}:{math.floor((I_Pointer - 1) / 8) + 1}:O.{(I_Pointer - 1) % 8 }"
                else:
                    x = f"Q{str(math.floor((I_Pointer - 1) / 8))}.{str((I_Pointer - 1) % 8)}"
                I_Pointer+= 1
            elif not project.is_Murr and IO.signal_type == "DO":
                print("DO it is")
                if project.PLC == "Allen Bradley":
                    x = f"RACK{letters[panel_n]}:{math.floor((I_Pointer - 1) / 8) + 1}:O.{(I_Pointer - 1) % 8 }"
                    I_Pointer+= 1
                    print(x)
                else:
                    x = f"Q{str(math.floor((Q_Pointer - 1) / 8))}.{str((Q_Pointer - 1) % 8)}"
                    Q_Pointer+= 1
            IO.io_address =  x
            IO.save()
            worksheet.write(row, 6, IO.io_address)
            worksheet.write(row, 7, IO.actual_description)
            worksheet.write(row, 8, channel)
            worksheet.write(row, 9, IO.module_position)
            worksheet.write(row, 10, IO.panel_number)
            worksheet.write(row, 11, IO.location)
            if project.is_Murr:
                worksheet.write(row, 12, "X2" if row%2 == 0 else "X4")
                if ((row-1 % 16)+1) %2 == 0:
                    worksheet.write(row, 13, f'X{((row-1 % 16)+1) }')
                # worksheet.write(row, 12, f'X{((row-1 % 16)+1) }')
            row += 1
            IOOut = IO
        # Channel_Dict= {0:[0,1], 1:[2,3], 2:[4,5], 3:[6,7], 4:[8,9]}
    # print(IOOut.signal_type)
    # print(F'Panel number {panel} of I_Pointer count {I_Pointer}.')
    #Adding Input spares
    for i in range(16- ( ((I_Pointer-1)%16))):
        count = i+1
        worksheet, I_Pointer, Q_Pointer = add_spares(worksheet,row,project,IOOut, count, I_Pointer, Q_Pointer, panel_n, "DI")
        row += 1
        # print(I_Pointer)

    #Writing DOs to file
    if not project.is_Murr:
        # sourcery skip: low-code-quality
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        for IO in iolist:
            if IO.signal_type == "DO"  :
                channel = (row - 1) % 16 + 1
                worksheet.write(row, 0, row)
                worksheet.write(row, 1, IO.name)
                worksheet.write(row, 2, IO.code)
                worksheet.write(row, 3, IO.tag)
                worksheet.write(row, 4, IO.signal_type)
                worksheet.write(row, 5, IO.device_type)
                if IO.signal_type == "DI":
                    if project.PLC == "Allen Bradley":
                        x = f"RACK{letters[panel_n]}:{math.floor((I_Pointer - 1) / 8) + 1}:I.{(I_Pointer - 1) % 8 }"
                    else:
                        x = f"I{str(math.floor((I_Pointer - 1) / 8))}.{str((I_Pointer - 1) % 8)}"
                    I_Pointer+= 1
                elif IO.signal_type == "DO":
                    if project.PLC == "Allen Bradley":
                        x = f"RACK{letters[panel_n]}:{math.floor((I_Pointer - 1) / 8) + 1}:O.{(I_Pointer - 1) % 8 }"
                        I_Pointer+= 1
                    else:
                        x = f"Q{str(math.floor((Q_Pointer - 1) / 8))}.{str((Q_Pointer - 1) % 8)}"
                        Q_Pointer+= 1
                IO.io_address =  x
                IO.save()
                worksheet.write(row, 6, IO.io_address)
                worksheet.write(row, 7, IO.actual_description)
                worksheet.write(row, 8, channel)
                worksheet.write(row, 9, IO.module_position)
                worksheet.write(row, 10, IO.panel_number)
                worksheet.write(row, 11, IO.location)
                row += 1
                IOOut = IO
    # print(F'Panel number {panel} of I_Pointer count {Q_Pointer}.')
    #Adding Output spares
    if not project.is_Murr:

        if project.PLC == "Allen Bradley":
            for i in range(16- ( ((I_Pointer-1)%16))):
                count = i+1
                worksheet, I_Pointer, Q_Pointer = add_spares(worksheet,row,project,IOOut, count, I_Pointer, Q_Pointer, panel_n, "DO")
                row += 1
        else:
            for i in range(16- ( ((Q_Pointer-1)%16))):
                count = i+1
                worksheet, I_Pointer, Q_Pointer = add_spares(worksheet,row,project,IOOut, count, I_Pointer, Q_Pointer, panel_n, "DO")
                row += 1
    dup_format = workbook.add_format({'bg_color': '#FFC7CE','font_color': '#9C0006'})

    worksheet.conditional_format(f'D2:D{row}', {'type': 'duplicate','format': dup_format})
    # print(F'Panel number {panel} of count {I_Pointer}, {Q_Pointer}.')
    return workbook, I_Pointer, Q_Pointer


#EXporting IO List to Excel file
@login_required(login_url="/accounts/login")
def export_to_excel(request):
    project_id = request.session.get('project')
    project = get_object_or_404(Project, id=project_id)
    if project.is_Murr:
        iolist = IOList.objects.filter(project_id=project_id).order_by('order')
        # print('Its Murr')
    else:
        iolist = IOList.objects.filter(project_id=project_id).order_by('signal_type', 'location','order')
    if len(project.panel_numbers) > 2:
        panels = project.panel_numbers.split(",")
        print(panels)
    else:
        panels = [i.panel_number for i in iolist]
        panels =[*set(panels)]
        panels = sorted(panels)
    # print(panels)
    I_Pointer = 1
    Q_Pointer = 1
    output = BytesIO()
    # Feed a buffer to workbook
    workbook = xlsxwriter.Workbook(output)

    while None in panels:
        # removing None from list using remove method
        panels.remove(None)
    for panel_n, panel in enumerate(panels, start=0):
        panelIO = iolist.filter(panel_number=panel)
        if project.PLC == "Allen Bradley":
            I_Pointer = 1
        workbook, I_Pointer, Q_Pointer = write_sheet(panel, workbook, project, panelIO, I_Pointer, Q_Pointer , panel_n)

    workbook.close()
    output.seek(0)
    panel_counts = iolist.filter(tag__icontains='spare') \
                    .values('panel_number') \
                    .annotate(count=Count('tag', filter=Q(tag__icontains='spare'))) \
                    .values_list('panel_number', 'count')
    
    project.panels = dict(panel_counts)
    print(project.panels)
    project.save()
    response = HttpResponse(output.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    return response

#Get list of Clusters/ Modules
class ModuleListView(LoginRequiredMixin, TemplateView):
    template_name = 'update_data/update_module.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_groups = self.request.user.groups.values_list('name', flat=True)
        # if 'Managers' in user_groups:
        #     modules = Module.objects.all()
        # else:
        if self.request.user.groups.filter(name="Emulation"):
            modules= Module.objects.all()
        else:
            modules = Module.objects.filter(segment__in=user_groups)
        serializer = ModuleSerializer(modules, many=True)
        context['modules'] = serializer.data
        return context


#Delete Cluster / Module
def module_destroy(request, id):
    module = Module.objects.get(id=id)
    if request.user.groups.filter(name='Managers').exists() and request.user.groups.filter(name=module.segment).exists():
        module.delete()
        return redirect('/module_list')
    else :
        return HttpResponse("User does not have permissions to delete")

# form to add new module
@login_required(login_url="/accounts/login")
def create_module(request):
    if request.method == 'POST':
        form = ClusterForm(request.POST)
        user_groups = request.user.groups.values_list('name', flat=True)
        if form.is_valid() and form.cleaned_data['segment'] in user_groups:
            module = form.save(commit=False)
            module.created_by = request.user.get_full_name()
            module.save()
            request.session['module'] = module.id
            return redirect('module_list') 
        else:
            messages.error(request, f"Invalid form data or you don't have the required rights for this segment - {form.cleaned_data['segment']}.")
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

@method_decorator(login_required, name='dispatch')
class IolistView(View):

    context = {'segment': 'iolist'}


    def get(self, request, *args, **kwargs):
        project_id = kwargs.get('pk')
        iolists =IOList.objects.filter(project_id=project_id)
        project = get_object_or_404(Project, pk=project_id)
        if not request.user.groups.filter(name=project.segment).exists():
            return HttpResponseForbidden()
        self.context['project'] = project
        self.context['io_list'] = iolists
        return render(request, 'projects/iolist.html', self.context)
    

    def delete(self, request, *args, **kwargs):
        # sourcery skip: class-extract-method
        iolist = get_object_or_404(IOList, id=kwargs.get('pk'))
        project= iolist.project
        if not request.user.groups.filter(name=project.segment).exists():
            return HttpResponseForbidden()
        iolist.delete()
        redirect_url = reverse('iolist')
        
        response = {'valid': 'success', 'message': 'Item deleted successfully', 'redirect_url': redirect_url}
        return redirect((f'/iolist/{project.id}/get'))
    

    def edit(self, request, *args, **kwargs):
        iolist = get_object_or_404(IOList, id=kwargs.get('pk'))
        project_id = request.session.get('project')
        project = get_object_or_404(Project, pk=project_id)
        if not request.user.groups.filter(name=project.segment).exists():
            return HttpResponseForbidden()
        if request.method == 'POST':
            form = IOListForm(request.POST, instance=iolist)
            # print("It's Post")
            if form.is_valid():
                form.save()
                # print("It's Save")
                messages.success(request, 'Item updated successfully')
                redirect_url = reverse('iolist')
                response = {'valid': 'success', 'message': 'Item updated successfully', 'redirect_url': redirect_url}
                return redirect('iolist', project_id )
            else:
                print(form.errors)
        else:
            form = IOListForm(instance=iolist)
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
        try:
            project_id = request.session.get('project')
            project = get_object_or_404(Project, pk=project_id)
            print(project)
            segment = project.segment
        except:
            segment = "Test"
        print(segment)
        if not request.user.groups.filter(name= segment).exists():
            print("Not in group")
            return HttpResponseForbidden()

        elif kwargs.get('action') == 'delete':
            return self.delete(request, *args, **kwargs)
        elif kwargs.get('action') == 'edit':
            return self.edit(request, *args, **kwargs)
        else:
            return super().dispatch(request, *args, **kwargs)

# To delete IO in Detail view.
def delete_IO(request,pk):
    io_queryset = IOList.objects.filter(pk=pk)
    # print(io_queryset)
    if io_queryset.exists():
        io = io_queryset.first()
        project = io.project
        io.delete()
        io_list = IOList.objects.filter(project = project).order_by('-id')
        data = render_to_string('projects/iolist_in_add.html', {'io_list': io_list})
        return JsonResponse(({'success': True, 'data': data}))
        # return render(request, 'projects/iolist_in_add.html', {'io_list': iolists})
    else:
        return HttpResponseNotFound()

#Update IOList on details page
def update_IO(request,pk):
    io_queryset = IOList.objects.filter(pk=pk)
    if io_queryset.exists():
        io = io_queryset.first()
        project = io.project
        iolists = IOList.objects.filter(project=project).order_by('-id')
        return JsonResponse(({'success': True}))
        # return render(request, 'projects/iolist_in_add.html', {'io_list': iolists})
    else:
        return HttpResponseNotFound()


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
            # print("Deleted Cluster")
            return redirect('signals')
        else:
            return HttpResponse("User does not have permissions to delete")
    

    def add(self, request, *args, **kwargs):  # sourcery skip: extract-method
        module_id = request.session.get('module')
        module = get_object_or_404(Module, id= module_id)
        if request.method == 'POST':
            form = SignalsForm(request.POST, user=request.user)
            if form.is_valid():
                signal = form.save(commit=False)
                signal.created_by = request.user.get_full_name()
                signal.module = module
                signal.save()
                module.updated_at = datetime.now()
                module.save()
                return redirect('signals')
        else:
            form = SignalsForm(user=request.user)
        return render(request, 'update_data/edit_signal.html', {'form': form, 'module' : module})

    

    def edit(self, request, *args, **kwargs):
        signal = get_object_or_404(Signals, id=kwargs.get('pk'))
        if request.method == 'POST':
            form = SignalsForm(request.POST,user=request.user, instance=signal)
            
            if form.is_valid():
                form.save()
                messages.success(request, 'Item updated successfully')
                redirect_url = reverse('signals')
                response = {'valid': 'success', 'message': 'Item updated successfully', 'redirect_url': redirect_url}
                return redirect('signals')
            else:
                print(form.errors)
        else:
            form = SignalsForm(instance=signal, user=request.user)
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


