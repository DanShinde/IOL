from io import BytesIO
import json
import subprocess
from django.forms import inlineformset_factory
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views import View
import pandas as pd
from .utils import set_pagination
from django.contrib import messages
from django.db.models import Q
from django.views.generic import TemplateView
import xlsxwriter
from django.template.loader import render_to_string
from django.template import loader
from rest_framework.response import Response
from .serializers import SignalSerializer, ModuleSerializer
from .forms import ProjectForm, SignalsForm, IOListForm
from .models import Project, Module, Signals, IOList
from django.core import serializers
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required,permission_required
from django.contrib.auth import login, logout, authenticate
from django.http import QueryDict
# from .forms import ModuleForm
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
            project.save()
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
            Cluster =  signalData.module,
            created_by = request.user.get_full_name()
        )
        entry.save()
    io_list = IOList.objects.filter(project = project).order_by('-id')
    # print(io_list)
    data = serializers.serialize('json', io_list)

    return JsonResponse({'success': True, 'data': data})


#EXporting IO List to Excel file
@login_required(login_url="/accounts/login")
def export_to_excel(request):
    project_id = request.session.get('project')
    project = get_object_or_404(Project, id=project_id)
    iolist = IOList.objects.filter(project_id=project_id).order_by('location','signal_type')
    output = BytesIO()
    # Feed a buffer to workbook
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet(project.name)
    bold = workbook.add_format({'bold': True})
    columns = ["Project", "ModuleName",  "Code", "Tag", "Signal Type","Device Type", "Actual Description","Location"]
    # Fill first row with columns
    row = 0
    for i,elem in enumerate(columns):
        worksheet.write(row, i, elem, bold)
    row += 1
    # Now fill other rows with columns
    for IO in iolist:
        worksheet.write(row, 0, project.name)
        worksheet.write(row, 1, IO.name)
        worksheet.write(row, 2, IO.code)
        worksheet.write(row, 3, IO.tag)
        worksheet.write(row, 4, IO.signal_type)
        worksheet.write(row, 5, IO.device_type)
        worksheet.write(row, 6, IO.actual_description)
        worksheet.write(row, 7, IO.location)
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


def edit_module(request, id):
    module = get_object_or_404(Module, pk=id)
    signals = Signals.objects.filter(module=module)
    return render(request, 'update_data/edit_module.html', {'signals': signals})

def signal_delete(request, id):
    signal = Signals.objects.get(id=id)
    signal.delete()
    return redirect('/module_edit')

#####Commented signal view for now
# class SignalsView(View):
#     context = {'segment': 'signals'}


#     def get(self, request, pk=None, action=None):
#         if HttpRequest.is_ajax(request):
#             if pk and action == 'edit':
#                 edit_row = self.edit_row(pk)
#                 return JsonResponse({'edit_row': edit_row})
#             elif pk and not action:
#                 edit_row = self.get_row_item(pk)
#                 return JsonResponse({'edit_row': edit_row})

#         if pk and action == 'edit':
#             context, template = self.edit(request, pk)
#         else:
#             context, template = self.list(request)

#         if not context:
#             html_template = loader.get_template('page-500.html')
#             return HttpResponse(html_template.render(self.context, request))

#         return render(request, template, context)
#     # def get(self, request, pk=None, action=None):
#     #     if request.is_ajax():
#     #         if pk and action == 'edit':
#     #             edit_row = self.edit_row(pk)
#     #             return JsonResponse({'edit_row': edit_row})
#     #         elif pk and not action:
#     #             edit_row = self.get_row_item(pk)
#     #             return JsonResponse({'edit_row': edit_row})

#     #     if pk and action == 'edit':
#     #         context, template = self.edit(request, pk)
#     #     else:
#     #         context, template = self.list(request)

#     #     if not context:
#     #         html_template = loader.get_template('page-500.html')
#     #         return HttpResponse(html_template.render(self.context, request))

#     #     return render(request, template, context)

#     def post(self, request, pk=None, action=None):
#         self.update_instance(request, pk)
#         return redirect('signals')

#     def put(self, request, pk, action=None):
#         is_done, message = self.update_instance(request, pk, True)
#         edit_row = self.get_row_item(pk)
#         return JsonResponse({'valid': 'success' if is_done else 'warning', 'message': message, 'edit_row': edit_row})

#     def delete(self, request, pk, action=None):
#         signal = self.get_object(pk)
#         signal.delete()

#         redirect_url = None
#         if action == 'single':
#             messages.success(request, 'Item deleted successfully')
#             redirect_url = reverse('signals')

#         response = {'valid': 'success', 'message': 'Item deleted successfully', 'redirect_url': redirect_url}
#         return JsonResponse(response)

#     """ Get pages """

#     def list(self, request):
#         filter_params = None

#         search = request.GET.get('search')
#         if search:
#             filter_params = None
#             for key in search.split():
#                 if key.strip():
#                     if not filter_params:
#                         filter_params = Q(code__icontains=key.strip())
#                     else:
#                         filter_params |= Q(code__icontains=key.strip())

#         signals = Signals.objects.filter(filter_params) if filter_params else Signals.objects.all()

#         self.context['signals'], self.context['info'] = set_pagination(request, signals)
#         if not self.context['signals']:
#             return False, self.context['info']

#         return self.context, 'app/signals/list.html'

#     def edit(self, request, pk):
#         signal = self.get_object(pk)

#         self.context['signal'] = signal
#         self.context['form'] = SignalsForm(instance=signal)

#         return self.context, 'update_data/edit.html'

#     """ Get Ajax pages """

#     def edit_row(self, pk):
#         signal = self.get_object(pk)
#         form = SignalsForm(instance=signal)
#         context = {'instance': signal, 'form': form}
#         return render_to_string('app/signals/edit_row.html', context)

#     """ Common methods """

#     def get_object(self, pk):
#         signal = get_object_or_404(Signals, id=pk)
#         return signal
    
#     def update_instance(self, request, pk, is_urlencode=False):
#         signal = self.get_object(pk)
#         form_data = QueryDict(request.body) if is_urlencode else request.POST
#         form = SignalsForm(form_data, instance=signal)
#         if form.is_valid():
#             form.save()
#             if not is_urlencode:
#                 messages.success(request, 'Transaction saved successfully')

#             return True, 'Transaction saved successfully'

#         if not is_urlencode:
#             messages.warning(request, 'Error Occurred. Please try again.')
#         return False, 'Error Occurred. Please try again.'



class IolistView(View):
    context = {'segment': 'iolist'}

    def get(self, request, pk=None, action=None):
        project_id = request.session.get('project')
        iolists =IOList.objects.filter(project_id=project_id)
        self.context['io_list'] = iolists
        return render(request, 'projects/iolist.html', self.context)

    def delete(self, request, *args, **kwargs):
        # sourcery skip: class-extract-method
        iolist = get_object_or_404(IOList, id=kwargs.get('pk'))
        iolist.delete()
        redirect_url = reverse('iolist')
        
        response = {'valid': 'success', 'message': 'Item deleted successfully', 'redirect_url': redirect_url}
        
        # return JsonResponse(response)
        return redirect('iolist')

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
        context = {
            'form': form,
            'iolist': iolist,
            'action': 'edit',
        }
        return render(request, 'projects/edit_iolist.html', context)

    def dispatch(self, request, *args, **kwargs):
        if kwargs.get('action') is None:
            return self.get(request, *args, **kwargs)
        elif kwargs.get('action') == 'delete':
            return self.delete(request, *args, **kwargs)
        elif kwargs.get('action') == 'edit':
            return self.edit(request, *args, **kwargs)
        else:
            return super().dispatch(request, *args, **kwargs)



#Work in progress

# class ModuleView(View):
#     context = {'segment': 'iolist'}

#     def get(self, request, pk=None, action=None):
#         project_id = request.session.get('project')
#         iolists =IOList.objects.filter(project_id=project_id)
#         self.context['io_list'] = iolists
#         return render(request, 'update_data/modulelist.html', self.context)

#     def delete(self, request, *args, **kwargs):
#         # sourcery skip: class-extract-method
#         iolist = get_object_or_404(IOList, id=kwargs.get('pk'))
#         iolist.delete()
#         redirect_url = reverse('iolist')
        
#         response = {'valid': 'success', 'message': 'Item deleted successfully', 'redirect_url': redirect_url}
        
#         # return JsonResponse(response)
#         return redirect('iolist')

#     def edit(self, request, *args, **kwargs):
#         iolist = get_object_or_404(Signals, id=kwargs.get('pk'))
#         if request.method == 'POST':
#             form = IOListForm(request.POST, instance=iolist)
#             print("It's Post")
#             if form.is_valid():
#                 form.save()
#                 print("It's Save")
#                 messages.success(request, 'Item updated successfully')
#                 redirect_url = reverse('iolist')
#                 response = {'valid': 'success', 'message': 'Item updated successfully', 'redirect_url': redirect_url}
#                 return redirect('iolist')
#             else:
#                 print(form.errors)
#         else:
#             form = IOListForm(instance=iolist)
#         context = {
#             'form': form,
#             'iolist': iolist,
#             'action': 'edit',
#         }
#         return render(request, 'update_data/edit_module.html', context)

#     def dispatch(self, request, *args, **kwargs):
#         if kwargs.get('action') is None:
#             return self.get(request, *args, **kwargs)
#         elif kwargs.get('action') == 'delete':
#             return self.delete(request, *args, **kwargs)
#         elif kwargs.get('action') == 'edit':
#             return self.edit(request, *args, **kwargs)
#         else:
#             return super().dispatch(request, *args, **kwargs)



