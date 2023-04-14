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
    template_name='sorting/sorting.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = IOList.objects.first()
        return context

    def get_queryset(self, *args, **kwargs):
        project = self.request.session.get('project')
        print(project, kwargs.get('project_id'))
        project_ins = get_object_or_404(Project, pk=project)
        if project_ins.is_Murr:
            return IOList.objects.filter(project_id=project).order_by(
                'panel_number',  'order' # 'cluster_number',
            )
        else:
            return IOList.objects.filter(project_id=project).order_by(
                'panel_number', 'order', 'signal_type', 'location'
            )
    
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
    temp_Add = 0
    for idx, tag_key in enumerate(tag_pk_list, start=1):
        tag = io_list_dict[tag_key]
        if project.is_Murr and ((idx - temp_Add) % 16 ) in [15,16]:
            temp_Add += 2

        tag.order = (((idx-1)//14)*2) + idx         #idx + temp_Add
        # print(f'Order is {tag.order}')
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

# Order update by editing order number in table
@csrf_exempt
def order_update(request, pk, action):
    iolist = get_object_or_404(IOList, pk=pk)
    if action == 'update':
        parts = request.body.decode('utf-8').split("=")
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