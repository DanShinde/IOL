from django.shortcuts import render
from iol.models import ProjectReport
import pandas as pd
from datetime import datetime


def format_month_year(period):
    label_str = str(period)  # Convert Period object to string
    year, month = label_str.split('-')
    month_name = datetime.strptime(f'{year}-{month}', '%Y-%m').strftime('%B %Y')
    return month_name

def Trends():
    queryset = ProjectReport.objects.all()
    data = pd.DataFrame(queryset.values('project', 'updated_at', 'updated_by', 'created_at', 'created_by', 'segment'))

    # Pivot by segment
    pivot = pd.pivot_table(data, values='project', columns='segment', aggfunc='count', fill_value=0)

    # Format 'created_at' to month and year
    data['created_at'] = pd.to_datetime(data['created_at']).dt.to_period('M')

    # Pivot by month and year
    pivot2 = pd.pivot_table(data, values='project', columns='created_at', aggfunc='count', fill_value=0)

    # Format column labels in pivot2
    pivot2.columns = map(format_month_year, pivot2.columns)

    return pivot.to_json(), pivot2.to_json()





def home(request):
    pivot, pivot2 = Trends()
    context = {
        'pivot': pivot,
        'pivot2': pivot2,

    }
    return render(request, 'dashboard/dash.html', context)
