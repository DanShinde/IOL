from django.shortcuts import get_object_or_404
from iol.models import Project
from iol.models import IOList
from django.db.models import Max

# def get_max_order(project) -> int:
#     IOs = IOList.objects.filter(project_id = project).aggregate(Max('order'))
#     return IOs['order__max'] + 1 if len(IOs)>0 else 1

def get_max_order(project) -> int:
    IOs = IOList.objects.filter(project_id = project).aggregate(Max('order'))
    order = max(IOs['order__max'] + 1, 1) if IOs['order__max'] is not None else 1
    # project = get_object_or_404(Project, pk=project)
    if project.is_Murr and (order - 1) % 16 + 1 in [15,16]:
        
        order+=2
    # print(f'order is {order}',f'Mod is {(order - 1) % 16 + 1}')
    return order
