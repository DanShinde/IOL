import json
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from .forms import ProjectForm
from .models import Project, Module, Signals, IOList
from django.core import serializers

def create_project(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save()
            return redirect('project_list') 
    else:
        form = ProjectForm()
    return render(request, 'create_project.html', {'form': form})

def project_list(request):
    projects = Project.objects.all()
    return render(request, 'project_list.html', {'projects': projects})
#Tag = f"{name}_{equipment_code}_{code}"

def project_detail(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    modules = Module.objects.all()

    # if request.method == 'POST':
    #     module_id = request.POST.get('module')
    #     module = get_object_or_404(Module, pk=module_id)
    #     signals = get_signals_for_module(module)
    # else:
    signals = None
    request.session['project'] = project_id

    return render(request, 'project_detail.html', {'project': project, 'modules': modules, 'signals': signals})

def get_signals_for_module(module):
    signals = Signals.objects.filter(module=module)
    data = serializers.serialize('json', signals)
    return data


def get_signals(request, module_id):
    module = get_object_or_404(Module, pk=module_id)
    signals = get_signals_for_module(module)
    return HttpResponse(signals, content_type='application/json')

def get_filtered_signals(request):
    selected_module = request.GET.get('module')
    signals = Signals.objects.filter(module=selected_module).values()#.values('code')
    #print(signals)
    return JsonResponse({'signals': list(signals)})

def add_signals(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        signal_ids = data.get('signals', [])
        module_name = data.get('module_name')
        project_id = request.session.get('project')
        project = get_object_or_404(Project, pk=project_id)
        print(project_id)
        print(signal_ids)
        print(module_name)
        for signal in signal_ids:
            signalData = Signals.objects.get(id=signal)
            if signalData.signal_type == "DI":
                pre = "Ix_"
            elif signalData.signal_type == "DO":
                pre = "Qx_"
            else:
                pre = "Encoder_"
            print(signalData.module)
            module = signalData.module.values_list('id').first()
            #module = module.replace(',','')
            print(module)
            entry = IOList(project =project, name = module_name, 
                           equipment_code = signalData.equipment_code, code = signalData.code,
                           tag = pre+ module_name+"_"+signalData.code,
                           signal_type = signalData.signal_type, 
                           actual_description = signalData.component_description +", "+ signalData.function_purpose
                           )
            entry.save()
            entry.modules.set(module)


        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False, 'message': 'Invalid request method.'})
