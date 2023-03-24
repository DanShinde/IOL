from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.generic import ListView
from django.core import serializers
from iol.models import IOList
# Create your views here.

class IOListView(ListView):
    model = IOList
    context_object_name = 'iolists'
    template_name='sorting/sorting.html'

    def get_queryset(self, *args, **kwargs):
        project = self.request.session.get('project')
        print(project, kwargs.get('project_id'))
        IOs = IOList.objects.filter(project_id = project).order_by('panel_number', 'order','signal_type', 'location')
        return IOs
    
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
    io_list_dict = {tag.pk: tag for tag in io_list_queryset}
    for idx, tag_key in enumerate(tag_pk_list, start=1):
        tag = io_list_dict[tag_key]
        tag.order = idx
    IOList.objects.bulk_update(io_list_queryset, ['order'])
    data = serializers.serialize('json', io_list_queryset)
    return JsonResponse({"iolists": data})


    # order_list = request.POST.getlist('iolists')
    # print(order_list)
    # tag_pk_list = order_list[0].split(',')
    # tag_pk_list = [int(pk) for pk in tag_pk_list]
    # Tags = []
    # for idx, tag_key in enumerate(tag_pk_list, start=1) :
    #     print("------------------------------")
    #     Tag = IOList.objects.get(pk= tag_key)
    #     print(f'Id is {idx} and key is {tag_key}, {Tag.order}.')
    #     Tag.order = idx
    #     Tag.save()
    #     Tags.append(Tag)
    #     Tag = IOList.objects.get(pk= tag_key)
    #     print(Tag.order)
    # print(Tags)
    # data = serializers.serialize('json', Tags)
    # return JsonResponse({"iolists": data}) 


