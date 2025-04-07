from datetime import datetime
from io import BytesIO
import json
from django.http import HttpResponse, JsonResponse, HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import ListView
from django.core import serializers
import numpy as np
import pandas as pd
import requests
from iol.models import IOList, Project
from rest_framework.response import Response
from rest_framework.views import APIView
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
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
def save_iolist_Panels(request):

    data = request.data.get("fieldIOs", [])

    for entry in data:
        try:
            io = IOList.objects.get(id=entry["id"])
            io.save()
        except IOList.DoesNotExist:
            continue

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
        queryset = IOList.objects.filter(iomodule_name=selectedIOModule, project=project, panel_number=panel_number).order_by('panel_number', 'order')
    else:
        queryset = IOList.objects.filter(iomodule_name=selectedIOModule, project=project).order_by('order')

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
    )
    # Retrieve page number from session, default to 1 if not found
    page_number = request.session.get('page_number', 1)
    panel_number = request.GET.get('panel_number')
    if panel_number and panel_number != 'None':
        return redirect('grouping2', project_id=project.id, page_number=page_number,panel_number=panel_number) 
    else:
        return redirect('grouping2', project_id=project.id, page_number=page_number) 
    



def ExportIOListfromV1(project_name):
    # Fetch data from the external API
    project = get_object_or_404(Project, name=project_name)

    if project.is_Murr:
        iolist = IOList.objects.filter(project=project).order_by('iomodule_name','module_position', 'order')
    else:
        iolist = IOList.objects.filter(project=project).order_by('signal_type', 'location', 'iomodule_name','module_position', 'order')

    
    if not iolist:
        return HttpResponse("No IO list data available", status=204)
    
    # Prepare data for DataFrame
    io_data = []
    for item in iolist:
        io_data.append([
            item.id,
            item.name,
            item.code,
            item.tag,
            item.signal_type,
            item.io_address,
            item.device_type,
            item.actual_description,
            item.panel_number,
            item.node,  # IO Module Name
            item.module_position,
            item.channel,
            None,  # Pin (not available in data)
            item.location,  # Remarks (not available in data)
            None   # DataType (not available in data)
        ])
    
    # Convert to DataFrame
    columns = ["Sr.No", "Equipment Name", "Code", "Tag", "Signal Type", "I/O Address", 
                "Device Type", "Function Description", "Panel Number", "IO Module Name", 
                "Module Position", "Channel", "Pin",  "Remarks", "DataType"]
    df = pd.DataFrame(io_data, columns=columns)
    
    # Extract unique panels
    panels = df['Panel Number'].unique()

    # Create an in-memory Excel file
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')

    field_data = pd.DataFrame(columns=columns)
    Sheets = {}
    # Iterate over panels and write each panel's data to a separate sheet
    for panel in panels:
        if project.is_Murr:
            panel_data = df[(df['Panel Number'] == panel) & (df['Remarks'] == "CP")].reset_index(drop=True)
        else:
            panel_data = df[(df['Panel Number'] == panel) ].reset_index(drop=True)
        # Create a sequence for I/O Address (0.0, 0.1, ..., 0.7, 1.0, ..., etc.)
        num_rows = len(panel_data)
        sequence = np.floor(np.arange(num_rows) / 8) + (np.arange(num_rows) % 8) / 10.0
        panel_data.loc[:, 'I/O Address'] = sequence
        
        # Add prefix based on Signal Type ('DI' -> 'I', 'DO' -> 'Q')
        panel_data['I/O Address'] = panel_data.apply(
            lambda row: f"I{row['I/O Address']}" if row['Signal Type'] == 'DI' else f"Q{row['I/O Address']}",
            axis=1
        )
        Sheets[panel] = panel_data

        # Extract numerical part of the 'Panel Number' (e.g., 'CC01' → '1')
        panel_number_numeric = ''.join(filter(str.isdigit, panel)).lstrip('0')
        io_module_name = f"IO{panel_number_numeric}"

        # Assign the generated IO Module Name
        panel_data['IO Module Name'] = io_module_name + '01'

        # Assign Module Position: 1 for first 16, 2 for next 16, and so on
        panel_data["Module Position"] = (panel_data.index // 16) + 1

        # Assign Channel: 1 to 16, then repeat
        panel_data["Channel"] = (panel_data.index % 16) + 1  
        panel_data["Pin"] = "-"
        panel_data["DataType"] = "Bool"
        panel_data["Remarks"] = ""



        # ---- Field Devices ----
        # Filter data for 'FD' (Field Devices)
        if project.is_Murr:
            current_field_data = df[(df['Panel Number'] == panel) & (df['Remarks'] == "FD")].copy()  # Use .copy()
        else:
            current_field_data = pd.DataFrame(columns=columns)
            

        if not current_field_data.empty:


            # Generate I/O Address sequence for field devices (1000.0, 1000.1, ..., 1001.7, ...)
            num_rows_field = len(current_field_data)  # Get length after appending
            field_sequence = 1000.0 + np.floor(np.arange(num_rows_field) / 8) + (np.arange(num_rows_field) % 8) / 10.0

            # Assign the sequence
            current_field_data.loc[:, 'I/O Address'] = field_sequence

            # Add prefix ('DI' -> 'I', 'DO' -> 'Q')
            current_field_data['I/O Address'] =current_field_data.apply(
                lambda row: f"I{row['I/O Address']}" if row['Signal Type'] == 'DI' else f"Q{row['I/O Address']}",
                axis=1
            )

            # Assign IO Module Name
            # Generate IO Module Names: Start from "02", increment every 16 rows
            module_numbers = (2 + np.arange(num_rows_field) // 16).astype(str).tolist()

            # Assign the generated IO Module Names to 'IO Module Name'
            current_field_data['IO Module Name'] = [f"IO{panel_number_numeric}{num.zfill(2)}" for num in module_numbers]

            # Set Module Position to '-'
            current_field_data['Module Position'] = '-'
            current_field_data['DataType'] = 'Bool'
            current_field_data['Remarks'] = ''
            
            # Assign Channel values (X0, X1, ..., X7, repeating every 2 rows)
            current_field_data['Channel'] = [f"X{(i // 2) % 8}" for i in range(len(current_field_data))]

            # Assign Pin values (alternating between Pin 4 and Pin 2)
            current_field_data['Pin'] = ['Pin 4' if i % 2 == 0 else 'Pin 2' for i in range(len(current_field_data))]
            # Append to the main field_data DataFrame
            field_data = pd.concat([field_data, current_field_data], ignore_index=True)


    UpdateIOModuleName(Sheets, field_data)
    
    for sheet in Sheets:
        Sheets[sheet].loc[:, "Sr.No"] = range(1, len(Sheets[sheet]) + 1)  # Update existing column
        Sheets[sheet].to_excel(writer, sheet_name=sheet[:31], index=False)
    field_data.loc[:, "Sr.No"] = range(1, len(field_data) + 1)  # Update existing column
    field_data.to_excel(writer, sheet_name="PLC01-Field IO", index=False)

    workbook = writer.book
    border_format = workbook.add_format({'bottom': 2})  # Thick bottom border

    for sheet_name, worksheet in writer.sheets.items():
        num_rows = worksheet.dim_rowmax + 1  # Get the actual number of rows in the sheet
        for i in range(17, num_rows, 16):  # Start from row 17 (skipping header), then every 16 rows
            worksheet.set_row(i - 1, None, border_format)  # Adjust for 0-based indexing


    # Save the Excel file to memory
    writer.close()
    output.seek(0)

    
    return output




# Update IOModuleName while generating IO List
def UpdateIOModuleName(panel_data_dict, field_data):
    try:
        # Prepare a unified list for both panel and field data
        io_update_data = []

        # Process panel data
        for panel_number, panel_df in panel_data_dict.items():
            panel_entries = panel_df[['Sr.No', 'IO Module Name']].copy()
            panel_entries.rename(columns={'Sr.No': 'id', 'IO Module Name': 'iomodule_name'}, inplace=True)
            io_update_data.extend(panel_entries.to_dict(orient="records"))

        # Process field data
        field_entries = field_data[['Sr.No', 'IO Module Name']].copy()
        field_entries.rename(columns={'Sr.No': 'id', 'IO Module Name': 'iomodule_name'}, inplace=True)
        io_update_data.extend(field_entries.to_dict(orient="records"))

        for entry in io_update_data:
            try:
                io = IOList.objects.get(id=entry["id"])
                io.iomodule_name = entry["iomodule_name"]
                io.save()
            except IOList.DoesNotExist:
                continue

        return Response({"message": "I/O List saved successfully!"})

    except Exception as e:
        print(f"Error processing data: {str(e)}")
        return None

#Re-Assign IOs
def rearrange_ios(request, project_name, page_number):
    # Fetch data from the external API
    project = get_object_or_404(Project, name=project_name)

    if project.is_Murr:
        iolist = IOList.objects.filter(project=project).order_by('module_position', 'order')
    else:
        iolist = IOList.objects.filter(project=project).order_by('signal_type', 'location', 'module_position', 'order')

    
    if not iolist:
        return HttpResponse("No IO list data available", status=204)
    
    # Prepare data for DataFrame
    io_data = []
    for item in iolist:
        io_data.append([
            item.id,
            item.name,
            item.code,
            item.tag,
            item.signal_type,
            item.io_address,
            item.device_type,
            item.actual_description,
            item.panel_number,
            item.node,  # IO Module Name
            item.module_position,
            item.channel,
            None,  # Pin (not available in data)
            item.location,  # Remarks (not available in data)
            None   # DataType (not available in data)
        ])
    
    # Convert to DataFrame
    columns = ["Sr.No", "Equipment Name", "Code", "Tag", "Signal Type", "I/O Address", 
                "Device Type", "Function Description", "Panel Number", "IO Module Name", 
                "Module Position", "Channel", "Pin",  "Remarks", "DataType"]
    df = pd.DataFrame(io_data, columns=columns)
    
    # Extract unique panels
    panels = df['Panel Number'].unique()

    # Create an in-memory Excel file
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')

    field_data = pd.DataFrame(columns=columns)
    Sheets = {}
    # Iterate over panels and write each panel's data to a separate sheet
    for panel in panels:

        panel_data = df[(df['Panel Number'] == panel) & (df['Remarks'] == "CP")].reset_index(drop=True)
        
        # Sort by 'Signal Type'
        panel_data = panel_data.sort_values(by='Signal Type').reset_index(drop=True)
        panelIOs = IOList.objects.filter(project=project, panel_number=panel).order_by('signal_type')
        for idx, io in enumerate(panelIOs, start=1):
            io.order = idx

        # Optional optimization using bulk_update (Django 2.2+)
        IOList.objects.bulk_update(panelIOs, ['order'])


        # Create a sequence for I/O Address (0.0, 0.1, ..., 0.7, 1.0, ..., etc.)
        num_rows = len(panel_data)
        sequence = np.floor(np.arange(num_rows) / 8) + (np.arange(num_rows) % 8) / 10.0
        panel_data.loc[:, 'I/O Address'] = sequence
        
        # Add prefix based on Signal Type ('DI' -> 'I', 'DO' -> 'Q')
        panel_data['I/O Address'] = panel_data.apply(
            lambda row: f"I{row['I/O Address']}" if row['Signal Type'] == 'DI' else f"Q{row['I/O Address']}",
            axis=1
        )
        Sheets[panel] = panel_data

        # Extract numerical part of the 'Panel Number' (e.g., 'CC01' → '1')
        panel_number_numeric = ''.join(filter(str.isdigit, panel)).lstrip('0')
        io_module_name = f"IO{panel_number_numeric}"

        # Assign the generated IO Module Name
        panel_data['IO Module Name'] = io_module_name + '01'

        # Assign Module Position: 1 for first 16, 2 for next 16, and so on
        panel_data["Module Position"] = (panel_data.index // 16) + 1

        # Assign Channel: 1 to 16, then repeat
        panel_data["Channel"] = (panel_data.index % 16) + 1  
        panel_data["Pin"] = "-"
        panel_data["DataType"] = "Bool"
        panel_data["Remarks"] = ""



        # ---- Field Devices ----
        # Filter data for 'FD' (Field Devices)
        current_field_data = df[(df['Panel Number'] == panel) & (df['Remarks'] == "FD")].copy()  # Use .copy()

        if not current_field_data.empty:


            # Generate I/O Address sequence for field devices (1000.0, 1000.1, ..., 1001.7, ...)
            num_rows_field = len(current_field_data)  # Get length after appending
            field_sequence = 1000.0 + np.floor(np.arange(num_rows_field) / 8) + (np.arange(num_rows_field) % 8) / 10.0

            # Assign the sequence
            current_field_data.loc[:, 'I/O Address'] = field_sequence

            # Add prefix ('DI' -> 'I', 'DO' -> 'Q')
            current_field_data['I/O Address'] =current_field_data.apply(
                lambda row: f"I{row['I/O Address']}" if row['Signal Type'] == 'DI' else f"Q{row['I/O Address']}",
                axis=1
            )

            # Assign IO Module Name
            # Generate IO Module Names: Start from "02", increment every 16 rows
            module_numbers = (2 + np.arange(num_rows_field) // 16).astype(str).tolist()

            # Assign the generated IO Module Names to 'IO Module Name'
            current_field_data['IO Module Name'] = [f"IO{panel_number_numeric}{num.zfill(2)}" for num in module_numbers]

            # Set Module Position to '-'
            current_field_data['Module Position'] = '-'
            current_field_data['DataType'] = 'Bool'
            current_field_data['Remarks'] = ''
            
            # Assign Channel values (X0, X1, ..., X7, repeating every 2 rows)
            current_field_data['Channel'] = [f"X{(i // 2) % 8}" for i in range(len(current_field_data))]

            # Assign Pin values (alternating between Pin 4 and Pin 2)
            current_field_data['Pin'] = ['Pin 4' if i % 2 == 0 else 'Pin 2' for i in range(len(current_field_data))]
            # Append to the main field_data DataFrame
            field_data = pd.concat([field_data, current_field_data], ignore_index=True)



    UpdateIOModuleName(Sheets, field_data)

    return redirect('grouping2', project_id=project.id, page_number=page_number)


#Update IO Module name from Gouping Screen
def updateIOModuleSingle(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method.'})
    # Extract data from the request
    data = json.loads(request.body)
    io_id = data.get('io_id')
    new_iomodule = data.get('new_iomodule')
    io = get_object_or_404(IOList, id=io_id)
    io.iomodule_name = new_iomodule
    ios = IOList.objects.filter(project=io.project, iomodule_name=new_iomodule).order_by('panel_number', 'order').last()
    io.panel_number = ios.panel_number
    io.module_position = ios.module_position
    io.order = ios.order + 1
    io.location = ios.location
    io.save()
    return JsonResponse({'success': True, 'message': f'{io.tag} shifted to {io.iomodule_name} successfully!'})


