from django.shortcuts import render
from iol.models import ProjectReport
import pandas as pd

# Create your views here.
def Trends():  # sourcery skip: inline-immediately-returned-variable
    queryset= ProjectReport.objects.all()
    data = pd.DataFrame(queryset.values('project', 'updated_at', 'updated_by', 'created_at', 'created_by', 'segment'))
    # print(data)
    # pivot  = data.pivot(columns='segment', values= ['segment'])index='created_by',
    pivot = pd.pivot_table(data, values='project',  columns='segment', aggfunc='count', fill_value=0)
    print(pivot.to_json)
    return pivot.to_json


def home(request):
    pivot = Trends()
    context = {
        'pivot': pivot,
    }
    return render(request, 'dashboard/dash.html', context)
