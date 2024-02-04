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
    data['created_at'] = pd.to_datetime(data['created_at']).dt.to_period('M')
    pivot2 = pd.pivot_table(data, values='project',  columns='created_at', aggfunc='count', fill_value=0)
    print(pivot2.to_json)

    return pivot.to_json, pivot2.to_json


def home(request):
    pivot, pivot2 = Trends()
    context = {
        'pivot': pivot,
        'pivot2': pivot2,

    }
    return render(request, 'dashboard/dash.html', context)
