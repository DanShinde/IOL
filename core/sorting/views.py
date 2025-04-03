from datetime import datetime
import json
from django.http import HttpResponse, JsonResponse, HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import ListView
from django.core import serializers
from iol.models import IOList, Project
from rest_framework.response import Response
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
    new_tag_name = "Ix_SPARE"

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
    page_number = request.session.get('current_page', 1)
    panel_number = request.GET.get('panel_number')
    if panel_number and panel_number != 'None':
        return redirect('grouping2', project_id=project.id, page_number=page_number,panel_number=panel_number) 
    else:
        return redirect('grouping2', project_id=project.id, page_number=page_number) 
    