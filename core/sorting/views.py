import json
from django.http import HttpResponse, JsonResponse, HttpResponseNotFound
from django.shortcuts import get_object_or_404, render
from django.views.generic import ListView
from django.core import serializers
from iol.models import IOList, Project
from django.template.loader import render_to_string
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
    else:
        distinct_positions = IOList.objects.filter(project=project).values_list('module_position', flat=True).distinct().order_by('module_position')

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

# def ngroup_view(request):
#     page_number = 1 + request.session.get('page_number') 

#     project_id = request.session.get('project_id') 

#     project = get_object_or_404(Project, pk=project_id)
#     # Assuming 10 entries per page, calculate cluster_number based on page_number
#     module_position = page_number
#     request.session['page_number'] = module_position
#     request.session['project_id'] = project_id
    
#     queryset = IOList.objects.filter(module_position=module_position,project = project)
#     return render(request, 'sorting/grouping.html', {'iolists': queryset})

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

# def pgroup_view(request):
#     page_number =  request.session.get('page_number') - 1
#     project_id = request.session.get('project_id') 

#     project = get_object_or_404(Project, pk=project_id)
#     # Assuming 10 entries per page, calculate cluster_number based on page_number
#     module_position = page_number
#     request.session['page_number'] = page_number
#     request.session['project_id'] = project_id
    
#     queryset = IOList.objects.filter(cluster_number=module_position,project = project)
#     return render(request, 'sorting/grouping.html', {'iolists': queryset})

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