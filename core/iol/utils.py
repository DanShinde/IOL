import math
from urllib.parse import urlencode
from django.db.models import Max
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from .models import IOList

def add_Murr_spares(worksheet,row, project, IO, I_Pointer):
    channel = (row - 1) % 16 + 1
    worksheet.write(row, 0, row)
    worksheet.write(row, 1, "Spare")
    worksheet.write(row, 2, "Spare")

    worksheet.write(row, 4, IO.signal_type)
    worksheet.write(row, 5, "Spare_Signal")
    if project.is_Murr:
        x = f"I{str(math.floor((I_Pointer - 1) / 8))}.{str((I_Pointer - 1) % 8)}"
        worksheet.write(row, 3, f'Ix_Spare_Spare_{x}')
        I_Pointer+= 1
    worksheet.write(row, 6, x)
    worksheet.write(row, 7, "Spare Signal")
    worksheet.write(row, 8, channel)
    worksheet.write(row, 9, IO.panel_number)
    worksheet.write(row, 10, "CP")
    if project.is_Murr:
        worksheet.write(row, 11, "X4" if row%2 == 0 else "X2")
    return worksheet, I_Pointer
    
def get_max_cluster_number(project_id):
    max_cluster_number = IOList.objects.filter(project_id=project_id).aggregate(Max('cluster_number'))
    print(max_cluster_number)
    return max_cluster_number["cluster_number__max"] + 1 if max_cluster_number["cluster_number__max"] is not None else 1