from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.generic import ListView
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
    # order_pk = request.POST.getlist('tag_ids')
    # print(order_pk)
    # Tags = []
    # for idx, tag_key in enumerate(order_pk, start=1) :
    #     Tag = IOList.objects.get(pk= tag_key)
    #     Tag.order = idx
    #     Tag.save()
    #     Tags.append(Tag)
    # print(Tags)
    # return render (request, 'sorting/partials/list.html', {'tags' : Tags}) 
    print(request.POST.get('text'))
    return JsonResponse( {"tags" : "Hello"})

