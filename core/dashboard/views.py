from django.shortcuts import render
from iol.models import ProjectReport
import pandas as pd

# Create your views here.
def Trends():  # sourcery skip: inline-immediately-returned-variable
    queryset= ProjectReport.objects.all()
    data = pd.DataFrame(queryset)
    print(data)
    # pivot  = data.pivot(columns='segment', values= ['segment'])
    pivot = pd.pivot_table(data, values = 'project', index='created_by', columns = 'segment').reset_index()
    return pivot


def home(request):
    pivot = Trends()
    context = {
        'pivot': pivot,
    }
    return render(request, 'dashboard/dash.html', context)
