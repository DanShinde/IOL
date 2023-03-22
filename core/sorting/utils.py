from iol.models import IOList
from django.db.models import Max

# def get_max_order(project) -> int:
#     IOs = IOList.objects.filter(project_id = project).aggregate(Max('order'))
#     return IOs['order__max'] + 1 if len(IOs)>0 else 1

def get_max_order(project) -> int:
    IOs = IOList.objects.filter(project_id = project).aggregate(Max('order'))
    return max(IOs['order__max'] + 1, 1) if IOs['order__max'] is not None else 1
