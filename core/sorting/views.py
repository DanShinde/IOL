from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.generic import ListView
from django.core import serializers
from iol.models import IOList, Project
# Create your views here.

class IOListView(ListView):
    model = IOList
    context_object_name = 'iolists'
    template_name='sorting/sorting.html'

    def get_queryset(self, *args, **kwargs):
        project = self.request.session.get('project')
        print(project, kwargs.get('project_id'))
        project_ins = get_object_or_404(Project, pk=project)
        if project_ins.is_Murr:
            return IOList.objects.filter(project_id=project).order_by(
                'panel_number','order', 'cluster_number'
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
        if project.is_Murr and ((idx) % 16 ) in [15,16]:
            temp_Add += 2

        tag.order = idx + temp_Add
        print(f'Order is {tag.order}')
    
    IOList.objects.bulk_update(io_list_queryset, ['order'])
    data = serializers.serialize('json', io_list_queryset)
    return JsonResponse({"iolists": data})


from django.views.decorators.csrf import csrf_exempt

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


