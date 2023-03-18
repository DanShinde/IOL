from django.contrib import admin
from .models import *
# Register your models here.
from iol.models import Signals, Module, IOList, Project
from import_export import resources
from import_export.admin import ImportMixin, ExportMixin, ImportExportMixin


class SignalResource(resources.ModelResource):
    class Meta:
        model = Signals
        fields = '__all__'


@admin.register(Signals)
class SignalsAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ['id', 'equipment_code', 'code','component_description',
                    'function_purpose',	'device_type',	'signal_type',	
                    'remarks', 'segment', 'initial_state', 'location', 'module_id']

    resource_class = SignalResource




admin.site.register(IOList)
admin.site.register(Project)
admin.site.register(Module)