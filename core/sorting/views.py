from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.generic import ListView
from django.core import serializers
from iol.models import IOList
# Create your views here.

class IOListView(ListView):
    model = IOList
    context_object_name = 'tags'
    template_name='sorting/sorting.html'

    def get_queryset(self):
        project = self.request.session.get('project')
        IOs = IOList.objects.filter(project_id = project)
        return IOs
    
def delete_tag(request, pk):
    io = IOList.objects.get(pk= pk)
    project = request.session.get('project')
    io.delete()
    IOs = IOList.objects.filter(project_id = project)
    return render (request, 'sorting/partials/table.html', {'tags' : IOs}) 
    
def sort_IO(request):
    order_list = request.POST.getlist('tags')
    print(order_list)
    tag_pk_list = order_list[0].split(',')
    tag_pk_list = [int(pk) for pk in tag_pk_list]
    Tags = []
    for idx, tag_key in enumerate(tag_pk_list, start=1) :
        print("------------------------------")
        print(f'Id is {idx} and key is {tag_key}.')
        Tag = IOList.objects.get(pk= tag_key)
        Tag.order = idx
        Tag.save()
        Tags.append(Tag)
    print(Tags)
    data = serializers.serialize('json', Tags)
    return JsonResponse({"Tags": data}) 


