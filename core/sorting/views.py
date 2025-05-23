from datetime import datetime
from io import BytesIO
import json
from django.http import HttpResponse, JsonResponse, HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import ListView
import numpy as np
import pandas as pd
from iol.models import IOList, Project
from rest_framework.response import Response
from rest_framework.views import APIView
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
# Create your views here.


class IOListView(ListView):
    model = IOList
    context_object_name = 'iolists'
    template_name = 'sorting/sorting.html'

    def get_queryset(self):
        project_id = self.request.session.get('project')
        queryset = self.model.objects.filter(project_id=project_id)
        project= Project.objects.get(id=project_id)
        panel_number = self.request.GET.get('panel-number')
        print(panel_number)
        if panel_number:
            queryset = queryset.filter(panel_number=panel_number)

        if project.is_Murr:
            queryset = queryset.order_by('panel_number', 'module_position','order')
        else:
            queryset = queryset.order_by('panel_number', 'module_position','order', 'signal_type', 'location')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        project_id = self.request.session.get('project')
        context['project'] = Project.objects.get(pk=project_id)

        iolist = self.get_queryset()
        panel_numbers = iolist.order_by().values_list('panel_number', flat=True).distinct()
        context['panel_numbers'] = panel_numbers

        return context

"""


Keyword arguments:
argument -- description
Return: return_description


# class IOListView(ListView):
#     model = IOList
#     context_object_name = 'iolists'
#     template_name='sorting/sorting.html'

#     def filter_queryset(self, queryset):
#         panel_number = self.request.GET.get('panel_number')
#         if panel_number:
#             queryset = queryset.filter(panel_number=panel_number)
#         return queryset

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['project'] = IOList.objects.first()
#         iolist = IOList.objects.filter(project_id=self.request.session.get('project')).order_by('order')
#         panels = [i.panel_number for i in iolist]
#         panels =[*set(panels)]

#         # Get the distinct panel numbers in the current project
#         panel_numbers = IOList.objects.filter(project_id=self.request.session.get('project')).values_list('panel_number', flat=True).distinct()
#         context['panel_numbers'] = panels

#         return context

#     def get_queryset(self, *args, **kwargs):
#         project = self.request.session.get('project')
#         panel_number = self.request.GET.get('panel_number')
#         project_ins = get_object_or_404(Project, pk=project)
        
#         io_list_queryset = IOList.objects.filter(project_id=project) 
#         for idx, io in enumerate(io_list_queryset, start=1):
#             if project_ins.is_Murr:
#                 io.module_position =1 + ( (idx-1)//14) 
#                 io.save()

#         queryset = IOList.objects.filter(project_id=project)
#         if panel_number:
#             queryset = queryset.filter(panel_number=panel_number)

#         if project_ins.is_Murr:
#             queryset = queryset.order_by('panel_number', 'order')
#         else:
#             queryset = queryset.order_by('panel_number', 'order', 'signal_type', 'location')
#         return queryset
    
#     def post(self, request, *args, **kwargs):
#         data = json.loads(request.body)
#         selected_panel_number = data['panel_number']

#         queryset = self.get_queryset()
#         queryset = self.filter_queryset(queryset)

#         if selected_panel_number:
#             queryset = queryset.filter(panel_number=selected_panel_number)

#         # html = render_to_string('sorting/partials/table.html', {'iolists': queryset})
#         # return JsonResponse({'html': html})
#         data = render_to_string('sorting/partials/table.html', {'iolists': queryset})
#         return JsonResponse(({'success': True, 'data': data}))  
"""
    
def delete_tag(request, pk):
    io = IOList.objects.get(pk= pk)
    project = request.session.get('project')
    io.delete()
    IOs = IOList.objects.filter(project_id = project)
    return render (request, 'sorting/partials/table.html', {'iolists' : IOs}) 
    
def sort_IO(request):
    order_list = request.POST.getlist('iolists')
    tag_pk_list = [int(pk) for pk in order_list[0].split(',')]
    io_list_queryset = IOList.objects.filter(pk__in=tag_pk_list)
    project = io_list_queryset[0].project
    io_list_dict = {tag.pk: tag for tag in io_list_queryset}

    for idx, tag_key in enumerate(tag_pk_list, start=1):
        tag = io_list_dict[tag_key]
        tag.order = (((idx-1)//14)*2) + idx if project.is_Murr else idx
        tag.module_position = (idx-1)//14
                  #idx + temp_Add

    # io_list_queryset = IOList.objects.filter(project_id = project).order_by('order')
    IOList.objects.bulk_update(io_list_queryset, ['order'])
    data = render_to_string('sorting/partials/table.html', {'iolists': io_list_queryset})
    return JsonResponse(({'success': True, 'data': data}))
    # data = serializers.serialize('json', io_list_queryset)
    # return JsonResponse({"iolists": data})


from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view

# cluster number update by editing cluster number in table
@csrf_exempt
def cluster_number_update(request, pk, action):
    iolist = get_object_or_404(IOList, pk=pk)
    if action == 'update':
        parts = request.body.decode('utf-8').split("=")
        value = parts[1]
        iolist.cluster_number = int(value)
        iolist.save()
        return JsonResponse({'cluster_number': iolist.cluster_number})
    else:
        return JsonResponse({'error': 'Invalid request method'})


@csrf_exempt  # Exempt CSRF protection for this view
def module_position_update(request, pk, action):
    try:
        if request.method == 'PUT':
            # Get the module object
            iolist = get_object_or_404(IOList, pk=pk)

            # Get the new position value from the request data
            data = json.loads(request.body)
            new_position = data.get('new_position', '').strip()
            
            print(f"Request body: {json.dumps(request.body.decode('utf-8'))}")
            
            if not new_position:
                print("New position is missing")
                return JsonResponse({'success': False, 'error': 'New position is required.'}, status=400)

            # Update the position and save
            iolist.module_position = new_position
            iolist.save()

            # Return the updated module position as HTML
            return JsonResponse({
                'success': True,
                'html': f'<a href="#" class="editable module_position" contenteditable="true" data-pk="{pk}" hx-get="{request.path}" hx-trigger="blur changed" hx-vals=\'{{"new_position": this.innerText.trim()}}\' hx-swap="outerHTML">{iolist.module_position}</a>'
            })
        
        return JsonResponse({'success': False, 'error': 'Invalid HTTP method'}, status=405)

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# Order update by editing order number in table
@csrf_exempt
def order_update(request, pk, action):
    iolist = get_object_or_404(IOList, pk=pk)
    if action == 'update':
        print(request.body.decode('utf-8'))
        parts = request.body.decode('utf-8').split("=")
        print(parts)
        value = parts[1]
        iolist.order = int(value)
        iolist.save()
        return JsonResponse({'cluster_number': iolist.order})
    else:
        return JsonResponse({'error': 'Invalid request method'})


# To delete IO in Detail view.
def delete_in_Reorder(request,pk):
    io_queryset = IOList.objects.filter(pk=pk)
    # print(io_queryset)
    if io_queryset.exists():
        io = io_queryset.first()
        project = io.project
        io.delete()
        io_list = IOList.objects.filter(project = project).order_by('panel_number',  'order')
        data = render_to_string('sorting/partials/table.html', {'iolists': io_list})
        return JsonResponse(({'success': True, 'data': data}))
        # return render(request, 'projects/iolist_in_add.html', {'io_list': iolists})
    else:
        return HttpResponseNotFound()
    
#grouping IO List

from django.core.paginator import Paginator
from django.shortcuts import render


# def group_view(request,project_id, page_number):
#     request.session['page_number'] = page_number
#     request.session['project_id'] = project_id

#     project = get_object_or_404(Project, pk=project_id)
#     # Assuming 10 entries per page, calculate cluster_number based on page_number
#     module_position = page_number
    
#     queryset = IOList.objects.filter(module_position=module_position,project = project)
#     return render(request, 'sorting/grouping.html', {'iolists': queryset})

def group_view(request, project_id, page_number):
    request.session['page_number'] = page_number
    request.session['project_id'] = project_id

    project = get_object_or_404(Project, pk=project_id)
    panel_number = request.GET.get('panel_number')
    
    if panel_number and panel_number != 'None':
        panel_number = panel_number.strip()
        # Get distinct module_positions for the project filtered by panel_number
        distinct_positions = IOList.objects.filter(project=project, panel_number=panel_number).values_list('module_position', flat=True).distinct().order_by('module_position')
        ioModules = IOList.objects.filter(project=project, panel_number=panel_number).values_list('iomodule_name', flat=True).distinct().order_by('iomodule_name')
    else:
        distinct_positions = IOList.objects.filter(project=project).values_list('module_position', flat=True).distinct().order_by('module_position')
        ioModules = IOList.objects.filter(project=project).values_list('iomodule_name', flat=True).distinct().order_by('iomodule_name')


    # Get the module_position based on the page_number (index in distinct list)
    if page_number <= len(distinct_positions) and page_number > 0:
        module_position = distinct_positions[page_number - 1]  # 1-based index to 0-based list index
    else:
        module_position = distinct_positions[0]  # Default to first position if invalid
    if panel_number and panel_number != 'None':
        queryset = IOList.objects.filter(module_position=module_position, project=project, panel_number=panel_number).order_by('panel_number', 'order')
    else:
        queryset = IOList.objects.filter(module_position=module_position, project=project).order_by('order')

    panel_numbers = IOList.objects.filter(project=project).order_by().values_list('panel_number', flat=True).distinct()

    # Prepare the context dictionary to pass values to the template
    context = {
        'iolists': queryset,
        'panel_numbers': panel_numbers,
        'selected_panel_number': panel_number,  # Include the selected panel number in the context
        'project_id': project_id,
        'currentPageNumber': page_number,
    }

    return render(request, 'sorting/grouping.html', context)


def ngroup_view(request):
    page_number = 1 + request.session.get('page_number') 

    project_id = request.session.get('project_id') 

    project = get_object_or_404(Project, pk=project_id)
    panel_number = request.GET.get('panel-number')
    if panel_number != None:
    # Get distinct module_positions for the project
        distinct_positions = IOList.objects.filter(project=project, panel_number=panel_number).values_list('module_position', flat=True).distinct().order_by('module_position', 'order')
    else:
        distinct_positions = IOList.objects.filter(project=project).values_list('module_position', flat=True).distinct().order_by('module_position', 'order')
    # Get the module_position based on the page_number (index in distinct list)
    if page_number <= len(distinct_positions) and page_number > 0:
        module_position = distinct_positions[page_number - 1]  # 1-based index to 0-based list index
    else:
        module_position = distinct_positions[0]  # Default to first position if invalid
    
    request.session['page_number'] = page_number
    request.session['project_id'] = project_id
    
    queryset = IOList.objects.filter(module_position=module_position, project=project)
    panel_numbers = IOList.objects.filter(project=project).order_by().values_list('panel_number', flat=True).distinct()
    # Prepare the context dictionary to pass values to the template
    context = {
        'iolists': queryset,
        'panel_numbers': panel_numbers
    }
    return render(request, 'sorting/grouping.html', context)



def pgroup_view(request):
    page_number = -1 + request.session.get('page_number') 

    project_id = request.session.get('project_id') 

    project = get_object_or_404(Project, pk=project_id)
    panel_number = request.GET.get('panel-number')
    
    if panel_number != None:
    # Get distinct module_positions for the project
        distinct_positions = IOList.objects.filter(project=project,panel_number=panel_number).values_list('module_position', flat=True).distinct().order_by('module_position', 'order')
    else:
        distinct_positions = IOList.objects.filter(project=project).values_list('module_position', flat=True).distinct().order_by('module_position', 'order')
    # Get the module_position based on the page_number (index in distinct list)
    if page_number <= len(distinct_positions) and page_number > 0:
        module_position = distinct_positions[page_number - 1]  # 1-based index to 0-based list index
    else:
        module_position = distinct_positions[0]  # Default to first position if invalid
    
    request.session['page_number'] = page_number
    request.session['project_id'] = project_id
    
    queryset = IOList.objects.filter(module_position=module_position, project=project)
    
    return render(request, 'sorting/grouping.html', {'iolists': queryset})


@csrf_exempt
def update_clustern(request):

    if request.method == 'POST':
        data = json.loads(request.body)
        pk = data.get('pk')
        new_value = data.get('newValue')

        try:
            # Update your model instance with the new value
            instance = IOList.objects.get(pk=pk)
            instance.cluster_number = new_value
            instance.save()
            return JsonResponse({'success': True})
        except IOList.DoesNotExist:
            return JsonResponse({'error': 'Object not found'}, status=404)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    

class IOListClassifierView(View):
    template_name = "sorting/iolist_classifier.html"

    def get(self, request, project_id):
        if not project_id:
            return render(request, self.template_name, {"error": "No project selected."})

        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return render(request, self.template_name, {"error": "Invalid project."})

        iolist = IOList.objects.filter(project_id=project_id)


        # Store project_id in session
        request.session["project_id"] = project_id

        return render(
            request,
            self.template_name,
            {
                "project": project,
                "ios": iolist,
            },
        )
    

@api_view(["POST"])
@csrf_exempt
def save_iolist_Classify(request):

    field_data = request.data.get("fieldIOs", [])
    panel_data = request.data.get("panelIOs", [])

    # 1. Collect all IDs
    field_ids = [entry["id"] for entry in field_data]
    panel_ids = [entry["id"] for entry in panel_data]

    # 2. Fetch all relevant IOList entries in one query
    io_fields = IOList.objects.filter(id__in=field_ids)
    io_panels = IOList.objects.filter(id__in=panel_ids)

    # 3. Create ID to object map
    io_mapf = {io.id: io for io in io_fields}
    io_mapp = {io.id: io for io in io_panels}

    # 4. Update locations accordingly (CP takes priority if in both)

    for io in io_mapf:
        io_mapf[io].location = 'FD'

    for io in io_mapp:
        io_mapp[io].location = 'CP'  # Overwrites FD if also in field_ids

    # 5. Save updated objects (in bulk)
    IOList.objects.bulk_update(io_mapf.values(), ['location'])
    IOList.objects.bulk_update(io_mapp.values(), ['location'])
    return Response({"message": "I/O List saved successfully!"})


def group_view2(request, project_id, page_number):
    request.session['page_number'] = page_number
    request.session['project_id'] = project_id

    project = get_object_or_404(Project, pk=project_id)
    panel_number = request.GET.get('panel_number')
    
    if panel_number and panel_number != 'None':
        panel_number = panel_number.strip()
        # Get distinct module_positions for the project filtered by panel_number
        ioModules = IOList.objects.filter(project=project, panel_number=panel_number).values_list('iomodule_name', flat=True).distinct().order_by('iomodule_name')
    else:
        ioModules = IOList.objects.filter(project=project).values_list('iomodule_name', flat=True).distinct().order_by('iomodule_name')


    # Get the module_position based on the page_number (index in distinct list)
    if page_number <= len(ioModules) and page_number > 0:
        selectedIOModule = ioModules[page_number - 1]  # 1-based index to 0-based list index
    else:
        selectedIOModule = ioModules[0]  # Default to first position if invalid
    if panel_number and panel_number != 'None':
        queryset = IOList.objects.filter(iomodule_name=selectedIOModule, project=project, panel_number=panel_number).order_by('signal_type', 'order')
    else:
        queryset = IOList.objects.filter(iomodule_name=selectedIOModule, project=project).order_by('order')
        if queryset.first().location == 'CP':
            queryset = queryset.order_by('signal_type', 'order')

    panel_numbers = IOList.objects.filter(project=project).order_by().values_list('panel_number', flat=True).distinct()

    # Prepare the context dictionary to pass values to the template
    context = {
        'iolists': queryset,
        'panel_numbers': panel_numbers,
        'selected_panel_number': panel_number,  # Include the selected panel number in the context
        'project_id': project_id,
        'project_name': project.name,
        'currentPageNumber': page_number,
        'group2': True,
        'io_modules' : json.dumps(list(ioModules)),
        'selectedIOModule': selectedIOModule,
        'AllIos': json.dumps(
        list(IOList.objects.filter(project=project)
             .values('id', 'tag', 'iomodule_name')  # Fetch both `id` and `tag`
             .order_by('tag')),
        ensure_ascii=False
    ),
    }

    return render(request, 'sorting/grouping.html', context)



@login_required(login_url="/accounts/login")
def add_spare(request, ref_io, signal_type):
    if request.method != 'GET':
        return JsonResponse({'success': False, 'message': 'Invalid request method.'})

    # Fetch the reference IOList instance
    ref_io_signal = get_object_or_404(IOList, id=ref_io)

    # Fetch the related project and update timestamp
    project = get_object_or_404(Project, pk=ref_io_signal.project_id)
    project.updated_at = datetime.now()
    project.save()

    # Generate a new tag name (modify as per your naming convention)
    if signal_type == "DI":
        new_tag_name = "Ix_SPARE"
    else :
        new_tag_name = "Qx_SPARE"


    # Create a copy of the IOList entry with modified tag name
    new_io = IOList.objects.create(
        project=ref_io_signal.project,
        name=ref_io_signal.name,
        equipment_code="SPARE",
        code="SPARE",
        tag=new_tag_name,  # Only this field changes
        signal_type=signal_type,
        device_type="Spare Signal",
        actual_description=ref_io_signal.actual_description,
        panel_number=ref_io_signal.panel_number,
        node=ref_io_signal.node,
        rack=ref_io_signal.rack,
        module_position=ref_io_signal.module_position,
        terminal_block=ref_io_signal.terminal_block,
        terminal_number=ref_io_signal.terminal_number,
        channel=ref_io_signal.channel,
        location=ref_io_signal.location,
        io_address=ref_io_signal.io_address,
        Cluster=ref_io_signal.Cluster,
        order=ref_io_signal.order + 1,
        cluster_number=ref_io_signal.cluster_number,
        iomodule_name=ref_io_signal.iomodule_name,
        Demo_3d_Property= "",
        created_by = request.user.get_full_name()
    )
    # Retrieve page number from session, default to 1 if not found
    page_number = request.session.get('page_number', 1)
    panel_number = request.GET.get('panel_number')
    if panel_number and panel_number != 'None':
        return redirect('grouping2', project_id=project.id, page_number=page_number,panel_number=panel_number) 
    else:
        return redirect('grouping2', project_id=project.id, page_number=page_number) 
    

from django.db import transaction
import re

# Constants for configuration
PANEL_IO_MODULE_PREFIX = "IO"
FIELD_IO_MODULE_PREFIX = "IO"
PANEL_IO_START_ADDRESS = 0.0
FIELD_IO_START_ADDRESS = 1000.0
MODULE_SIZE = 16  # Number of IOs per module
pin_drc_offset_map = {
            "Sen1": 1.0,
            "Sen2": 1.1,
            "In1": 4.0,
            "In2": 4.1,
            "In3": 4.2,
            "In4": 4.3,
            "Out1": 3.0,
            "Out2": 3.1,
            "Out3": 3.2,
            "Out4": 3.3,
            "LeftPin4": 3.4,
            "LeftPin2": 3.0,
            "RightPin4": 3.6,
            "RightPin2": 3.2,
        }

def assign_io_addresses(project_id):
    """
    Assign IO addresses and module names to all IOs in the project.
    This should be called whenever IOs are added, moved, or reordered.
    """
    project = get_object_or_404(Project, id=project_id)
    
    with transaction.atomic():
        # List to collect all IOs that need updating
        ios_to_update = []
        if project.is_Murr:
            # Process panel IOs (location = 'CP')
            panel_ios = IOList.objects.filter(
                project=project, 
                location='CP'
            ).order_by('panel_number', 'signal_type', 'order')
        else:
            panel_ios = IOList.objects.filter(
                project=project, 
            ).order_by('panel_number','signal_type', 'order')
        
        tempIOAddress = PANEL_IO_START_ADDRESS
        
        for panel_number in project.panel_numbers.split(","):
            panel_num = re.sub(r'\D', '', panel_number).lstrip('0') or '0'
            base_module_name = f"{PANEL_IO_MODULE_PREFIX}{panel_num}01"
            
            # Get all IOs for this panel
            panel_io_group = panel_ios.filter(panel_number=panel_number)
            
            # Assign addresses and module info
            for idx, io in enumerate(panel_io_group):
                # Calculate address (0.0, 0.1, ..., 0.7, 1.0, etc.)
                io_address = tempIOAddress + ((idx % 8)/10.0) 
                io.io_address = f"I{io_address}" if io.signal_type == 'DI' else f"Q{io_address}"
                
                # Assign module position (1 for first 16 IOs, 2 for next 16, etc.)
                io.module_position = (idx // MODULE_SIZE) + 1
                io.iomodule_name = base_module_name
                io.channel = (idx % MODULE_SIZE) + 1
                io.pin = '-'
                
                # Add to update list
                ios_to_update.append(io)
                
                # If the address exceeds .7, move to the next decade
                if (idx % 8) == 7:
                    tempIOAddress = tempIOAddress + 1
            
            # After each panel, move to the next decade for the next panel
            tempIOAddress = (int(tempIOAddress) // 10 + 1) * 10

        tempFIOAddress = FIELD_IO_START_ADDRESS        
        # Process field IOs (location = 'FD')
        field_ios = IOList.objects.filter(
            project=project,
            location='FD'
        ).order_by('panel_number', 'order')
        
        for panel_number in project.panel_numbers.split(","):
            if not project.is_Murr:
                break
            panel_num = re.sub(r'\D', '', panel_number).lstrip('0') or '0'
            
            # Get all field IOs for this panel
            field_io_group = field_ios.filter(panel_number=panel_number)
            
            # Assign addresses and module info
            for idx, io in enumerate(field_io_group):
                io_address = tempFIOAddress + ((idx % 8)/10.0) 
                io.io_address = f"I{io_address}" if io.signal_type == 'DI' else f"Q{io_address}"
                
                module_num = 2 + (idx // MODULE_SIZE)
                io.iomodule_name = f"{FIELD_IO_MODULE_PREFIX}{panel_num}{str(module_num).zfill(2)}"
                io.module_position = '0'
                io.channel = f"X{(idx // 2) % 8}"
                io.pin = 'Pin 4' if idx % 2 == 0 else 'Pin 2'
                io.terminal_number = 'Pin 4' if idx % 2 == 0 else 'Pin 2'
                
                # Add to update list
                ios_to_update.append(io)
                
                if (idx % 8) == 7:
                    tempFIOAddress = tempFIOAddress + 1
            
            tempFIOAddress = (int(tempFIOAddress) // 100 + 1) * 100

        # Process DRC IOs
        tempDIOAddress = (int(tempFIOAddress) // 1000 + 1) * 1000
        drcIOs = IOList.objects.filter(
            project=project,
            location='DRC',
        ).order_by('panel_number','iomodule_name', 'order')
        
        for panel_number in project.panel_numbers.split(","):
            # Get all field IOs for this panel
            drcIOs_group = drcIOs.filter(panel_number=panel_number)
            drcIOs_DeviceList = list(drcIOs_group.values_list('iomodule_name', flat=True).distinct())
            base = tempDIOAddress
            step = 64
            drcIOs_DeviceList = set(drcIOs_DeviceList)

            module_address_map = {
                module: base + step * idx
                for idx, module in enumerate(drcIOs_DeviceList)
            }

            # Assign addresses and module info
            for idx, io in enumerate(drcIOs_group):
                letter = "I" if io.signal_type == "DI" else "Q"
                addr = module_address_map[io.iomodule_name] 
                addr += pin_drc_offset_map[io.pin]
                io.io_address = f"%{letter}{addr:.1f}"
                
                # Add to update list
                ios_to_update.append(io)
        # # Sort them by io_address (ignoring first 2 chars)
        # ios_to_update_sorted = sorted(
        #     ios_to_update,
        #     key=lambda x: (
        #         x.iomodule_name if x.iomodule_name is not None else '',
        #         x.io_address[2:] if x.io_address else ''
        #     )
        # )

        # Assign order values
        # for idx, io in enumerate(ios_to_update, start=1):
        #     io.order = idx
        # Perform a single bulk update for all IOs
        IOList.objects.bulk_update(
            ios_to_update,
            ['io_address', 'module_position', 'iomodule_name', 'channel', 'pin', 'terminal_number']
        )
                





def ExportIOListfromV1(project_id):
    """
    Export IO list to Excel using pre-assigned addresses.
    Doesn't modify any data - just exports what's in the database.
    """
    project = get_object_or_404(Project, id=project_id)
    
    # Get all IOs with their pre-assigned addresses
    iolist = IOList.objects.filter(project=project).order_by(
        'panel_number', 'location', 'iomodule_name', 'order'
    )
    
    if not iolist:
        return HttpResponse("No IO list data available", status=204)
    
    # Prepare data for export
    export_data = []
    for io in iolist:
        export_data.append({
            "Sr.No": io.id,
            "Equipment Name": io.name,
            "Code": io.code,
            "Tag": io.tag,
            "Signal Type": io.signal_type,
            "I/O Address": io.io_address,
            "Device Type": io.device_type,
            "Function Description": io.actual_description,
            "Panel Number": io.panel_number,
            "IO Module Name": io.iomodule_name,
            "Module Position": io.module_position,
            "Channel": io.channel,
            "Pin": getattr(io, 'pin', '-'),
            "Remarks": io.location,
            "DataType": "Bool"
        })
    
    # Create DataFrame
    df = pd.DataFrame(export_data)
    
    # Create Excel file
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        # Create sheets for each panel
        for panel in project.panel_numbers.split(","):
            if project.is_Murr:
                panel_data = df[(df['Panel Number'] == panel) & (df['Remarks'] == 'CP')]
            else:
                panel_data = df[(df['Panel Number'] == panel)]
            # Convert Channel to numeric and then sort
            panel_data['Channel'] = pd.to_numeric(panel_data['Channel'])
            panel_data.sort_values(by=['IO Module Name', 'Module Position', 'Channel'], inplace=True) # 'I/O Address',
            if not panel_data.empty:
                panel_data = panel_data.copy()
                panel_data['Sr.No'] = range(1, len(panel_data) + 1)
                print(panel_data.to_string(index=False))
                panel_data.to_excel(
                    writer,
                    sheet_name=panel[:31],  # Excel sheet name limit
                    index=False
                )
                worksheet = writer.sheets[panel[:31]]
                # Define border format (bottom border)
                border_format = workbook.add_format({'bottom': 1})  # 1 = thin border

                # Determine rows needing bottom border (last occurrence of Module Position)
                last_occurrences = panel_data.index[
                    panel_data['Module Position'] != panel_data['Module Position'].shift(-1)
                ].tolist()
                # Identify last occurrence of IO Module Name
                last_io_modules = panel_data.index[
                    panel_data['IO Module Name'] != panel_data['IO Module Name'].shift(-1)
                ].tolist()

                # Combine both lists and remove duplicates
                border_rows = sorted(set(last_occurrences + last_io_modules))
                # Apply bottom border formatting correctly (Excel indexing adjustment)
                for row in border_rows:
                    excel_row = panel_data.index.get_loc(row) + 1  # DataFrame to Excel row adjustment (header = row 0)
                    worksheet.set_row(excel_row, None, border_format)


            
        
        # Create field devices sheet
        field_data = df[df['Remarks'] == 'FD']
        if not field_data.empty and project.is_Murr:
            field_data = field_data.copy()
            field_data['Sr.No'] = range(1, len(field_data) + 1)
            # Create an alternating list: Pin4, Pin2, Pin4, Pin2, ...
            pins = ['Pin4', 'Pin2'] * (len(field_data) // 2 + 1)
            # field_data['Pin'] = pins[:len(field_data)]
            field_data.sort_values(by=['IO Module Name', 'Channel'], inplace=True)
            field_data.to_excel(
                writer,
                sheet_name="PLC01-Field IO",
                index=False
            )
            # Identify last occurrence of IO Module Name
            last_occurrences = field_data.index[
                    field_data['IO Module Name'] != field_data['IO Module Name'].shift(-1)
                ].tolist()
            worksheet = writer.sheets["PLC01-Field IO"]
            # Apply bottom border formatting correctly (Excel indexing adjustment)
            for row in last_occurrences:
                excel_row = field_data.index.get_loc(row) + 1  # DataFrame to Excel row adjustment (header = row 0)
                worksheet.set_row(excel_row, None, border_format)

        # Create DRC sheet
        drc_data = df[df['Remarks'] == 'DRC']
        print(drc_data)
        if not drc_data.empty:
            drc_data = drc_data.copy()
            drc_data['Sr.No'] = range(1, len(drc_data) + 1)
            drc_data.sort_values(by=['IO Module Name', 'Channel'], inplace=True)
            drc_data.to_excel(
                writer,
                sheet_name="PLC01-DRC",
                index=False
            )
                        # Identify last occurrence of IO Module Name
            last_io_modules = field_data.index[
                panel_data['IO Module Name'] != panel_data['IO Module Name'].shift(-1)
            ].tolist()
            worksheet = writer.sheets["PLC01-DRC"]
            # Apply bottom border formatting correctly (Excel indexing adjustment)
            for row in last_io_modules:
                excel_row = panel_data.index.get_loc(row) + 1  # DataFrame to Excel row adjustment (header = row 0)
                worksheet.set_row(excel_row, None, border_format)

    
    output.seek(0)
    return output

# Update the updateIOModuleSingle to trigger address reassignment
def updateIOModuleSingle(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method.'})
    
    data = json.loads(request.body)
    io_id = data.get('io_id')
    new_iomodule = data.get('new_iomodule')
    
    with transaction.atomic():
        io = get_object_or_404(IOList, id=io_id)
        io.iomodule_name = new_iomodule
        
        # Find last IO in the new module to determine position
        last_io = IOList.objects.filter(
            project=io.project,
            iomodule_name=new_iomodule
        ).order_by('order').last()
        
        if last_io:
            io.order = last_io.order + 1
            io.panel_number = last_io.panel_number
            io.module_position = last_io.module_position
            io.location = last_io.location
        else:
            # New module - set default values
            io.order = 1
            io.module_position = 1
        
        io.save()
        
        # Reassign addresses for the entire project
        assign_io_addresses(io.project.id)
    
    return JsonResponse({
        'success': True, 
        'message': f'{io.tag} moved to {io.iomodule_name} successfully!'
    })


@login_required
def reassign_ios(request, project_id, page_number=1):
    """
    Reassign all IO addresses and module positions for a project.
    This should be called when major changes are made to the IO list.
    """
    project = get_object_or_404(Project, id=project_id)
    
    try:
    # with transaction.atomic():
        # First assign proper ordering
        assign_io_ordering(project)
        
        # Then generate addresses based on the new ordering
        assign_io_addresses(project.id)
        
        request.session['success_message'] = "IO addresses successfully reassigned"
        print(request.session['success_message'])
    except ValidationError as e:
        request.session['error_message'] = f"Validation error: {str(e)}"
        print(request.session['error_message'])

    except Exception as e:
        request.session['error_message'] = f"Error reassigning IOs: {str(e)}"
        print(request.session['error_message'])

    # try:
    #     print(request.session['error_message'])
    # except:
    #     pass
    return redirect('grouping2', project_id=project.id, page_number=page_number)

def assign_io_ordering(project):

    return
    """
    Assign proper ordering to all IOs in the project based on their current grouping
    """
    with transaction.atomic():
        # Process Control Panel IOs
        panel_ios = IOList.objects.filter(
            project=project,
            location='CP'
        ).order_by('panel_number', 'signal_type', 'order')
        
        # Reset all orders first
        panel_ios.update(order=None)
        
        # Assign new orders grouped by panel and module
        current_order = 1
        all_ios_to_update = []
        for panel in project.panel_numbers.split(","):
            panel_ios_sorted = panel_ios.filter(panel_number=panel).order_by('signal_type', 'order')

            for io in panel_ios_sorted:
                io.order = current_order
                all_ios_to_update.append(io)
                current_order += 1

        # Bulk update all at once
        IOList.objects.bulk_update(all_ios_to_update, ['order'])
                
        # Process Field IOs
        field_ios = IOList.objects.filter(
            project=project,
            location='FD'
        ).order_by('panel_number', 'iomodule_name', 'order')
        
        # Reset all orders first
        field_ios.update(order=None)
        
        # Assign new orders to field devices
        for idx, io in enumerate(field_ios, start=1):
            io.order = idx
            io.save()


@login_required(login_url="/accounts/login")
def add_dccard(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method.'})
    data = json.loads(request.body)
    print(data)
    project_id = request.session.get('project')
    project = get_object_or_404(Project, pk=project_id)
    project.updated_at = datetime.now()
    project.save()
    module_name = data.get('module_name')
    panel_number = data.get('panel_number')
    cardType = data.get('card') 
    # this is a list of dicts:
    assignments_list = data.get('assignments', [])

    # convert it to a dict keyed by pin:
    assignments_dict = {
        item['pin']: {k: v for k, v in item.items() if k != 'pin'}  # Using pin as key instead of code
        for item in assignments_list
    }
    print(assignments_dict)
    if module_name == "":
            return JsonResponse({'success': False, 'message': 'Module name is required.'})
    # assume `project`, `panel_number`, `module_name`, `pre`, `cluster_number`,
    # `request` and `order` are already defined in your view
    if cardType == "Add RAT":
        for pin, assignment in assignments_dict.items():
            print(assignment[pin])
            entry = IOList(
                project=project,
                name=module_name,
                equipment_code=assignment['pin']['code'],
                code=assignment['code'],
                tag=("Ix_" if assignment['signal_type'] == "DI" else "Qx_")+module_name+"_"+assignment['code'],
                signal_type=assignment['signal_type'],
                device_type=assignment['device_type'],
                # actual_description=assignment['function_desc'],
                panel_number=panel_number,
                iomodule_name="RAT_"+module_name,
                location="DRC",
                channel=pin,
                pin=pin,
                created_by=request.user.get_full_name(),
                # order=assignment['order'],
            )
        rows = [
            # sr, equipment_name,    code,               tag,                     signal_type, io_address,    device_type,                          function_desc,                        panel_number, io_module_name,   module_position, channel, pin, terminal_no, remarks, data_type
            (1,  "MC08",             "ROLLER_PROXY",     "Ix_MC08_ROLLER_PROXY", "DI",        "%I30001.0",   "Proximity Sensor",                   "Proximity Sensor",                   "CC05",        "MC08_FRAT_CRD",   "-",             "Sen1",   "-", "-",          "",      "Bool"),
            (2,  "MC08",             "WHEEL_PROXY",      "Ix_MC08_WHEEL_PROXY",  "DI",        "%I30001.1",   "Proximity Sensor",                   "Proximity Sensor",                   "CC05",        "MC08_FRAT_CRD",   "-",             "Sen2",   "-", "-",          "",      "Bool"),
            (3,  "MC08",             "PPS",              "Ix_MC08_PPS",          "DI",        "%I30004.0",   "Retro Reflective Photo Sensor",      "Retro Reflective Photo Sensor",      "CC05",        "MC08_FRAT_CRD",   "-",             "In1",    "-", "-",          "",      "Bool"),
            (4,  "MC08",             "PORT2_DTS",        "Ix_MC08_PORT2_DTS",    "DI",        "%I30004.1",   "Retro Reflective Photo Sensor",      "Retro Reflective Photo Sensor",      "CC05",        "MC08_FRAT_CRD",   "-",             "In2",    "-", "-",          "",      "Bool"),
            (5,  "MC08",             "PORT3_DTS",        "Ix_MC08_PORT3_DTS",    "DI",        "%I30004.2",   "Retro Reflective Photo Sensor",      "Retro Reflective Photo Sensor",      "CC05",        "MC08_FRAT_CRD",   "-",             "In3",    "-", "-",          "",      "Bool"),
            (6,  "MC08",             "Spare1",           "Ix_MC08_Spare1",       "DI",        "%I30004.3",   "Retro Reflective Photo Sensor",      "Retro Reflective Photo Sensor",      "CC05",        "MC08_FRAT_CRD",   "-",             "In4",    "-", "-",          "",      "Bool"),
            (7,  "MC08",             "LIFTING_MDR_FWD",  "Qx_MC08_LIFTING_MDR_FWD","DO",      "%Q30003.0",   "Lift Mdr Fwd Command",               "Lift Mdr Fwd Command",               "CC05",        "MC08_FRAT_CRD",   "-",             "Out1",   "-", "-",          "",      "Bool"),
            (8,  "MC08",             "LIFTING_MDR_REV",  "Qx_MC08_LIFTING_MDR_REV","DO",      "%Q30003.1",   "Lift Mdr Rev Command",               "Lift Mdr Rev Command",               "CC05",        "MC08_FRAT_CRD",   "-",             "Out2",   "-", "-",          "",      "Bool"),
            (9,  "MC08",             "Spare2",           "Qx_MC08_Spare2",       "DO",        "%Q30003.2",   "Spare",                              "Spare",                              "CC05",        "MC08_FRAT_CRD",   "-",             "Out3",   "-", "-",          "",      "Bool"),
            (10, "MC08",             "Spare3",           "Qx_MC08_Spare3",       "DO",        "%Q30003.3",   "Spare",                              "Spare",                              "CC05",        "MC08_FRAT_CRD",   "-",             "Out4",   "-", "-",          "",      "Bool"),
        ]

        for (sr, equipment_name, code, tag, sig_type, io_addr, dev_type,
            func_desc, pnl_num, io_mod_name, mod_pos, pin,channel
            , term_no, remarks, dt) in rows:

            entry = IOList(
                project=project,
                name=module_name,
                equipment_code=code,
                code=code,
                tag=("Ix_" if sig_type == "DI" else "Qx_")+module_name+"_"+code,
                signal_type=sig_type,
                io_address=io_addr,
                device_type=dev_type,
                actual_description=func_desc,
                panel_number=panel_number,
                iomodule_name="RAT_"+module_name,
                location="DRC",
                channel=channel,
                pin=pin,
                created_by=request.user.get_full_name(),
                order=sr,
            )
            entry.save()
    elif cardType == "Add DRC":
        
        rows = [
            # sr, equipment_name,    code,               tag,               signal_type, io_address,    device_type,   function_desc,             panel_number,         io_module_name,   module_position, channel,      pin, terminal_no, remarks, data_type
            (1,  "MC08",             "LeftPin4",     "Ix_MC08_ROLLER_PROXY", "DI",        "",   "DRC Input",          "Spare Signal",                   "CC05",        "MC08_FRAT_CRD",   "-",             "LeftPin4",   "-", "-",          "",      "Bool"),
            (2,  "MC08",             "LeftPin2",     "Ix_MC08_WHEEL_PROXY",  "DI",        "",   "DRC Input",          "Spare Signal",                   "CC05",        "MC08_FRAT_CRD",   "-",             "LeftPin2",   "-", "-",          "",      "Bool"),
            (3,  "MC08",             "RightPin4",    "Ix_MC08_PPS",          "DI",        "",   "DRC Input",          "Spare Signal",                   "CC05",        "MC08_FRAT_CRD",   "-",             "RightPin4",  "-", "-",          "",      "Bool"),
            (4,  "MC08",             "RightPin2",    "Ix_MC08_PORT2_DTS",    "DI",        "",   "DRC Input",          "Spare Signal",                   "CC05",        "MC08_FRAT_CRD",   "-",             "RightPin2",  "-", "-",          "",      "Bool"),
        ]

        for (sr, equipment_name, code, tag, sig_type, io_addr, dev_type,
            func_desc, pnl_num, io_mod_name, mod_pos, pin,channel
            , term_no, remarks, dt) in rows:

            entry = IOList(
                project=project,
                name=module_name,
                equipment_code=code,
                code=code,
                tag=("Ix_" if sig_type == "DI" else "Qx_")+module_name+"_"+code,
                signal_type=sig_type,
                io_address=io_addr,
                device_type=dev_type,
                actual_description=func_desc,
                panel_number=panel_number,
                iomodule_name=module_name,
                location="DRC",
                channel=channel,
                pin=pin,
                created_by=request.user.get_full_name(),
                order=sr,
            )
            entry.save()
    io_list = IOList.objects.filter(project = project).order_by('-id')
    data = render_to_string('projects/iolist_in_add.html', {'io_list': io_list})
    return JsonResponse({'success': True, 'data': data})
