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
    list_filter = ('segment', 'module_id')
    search_fields = (
        "module_id",
        "equipment_code",
        "segment"
    )






class IOListResource(resources.ModelResource):
    class Meta:
        model = IOList
        fields = '__all__'


@admin.register(IOList)
class IOListAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ['id','tag', 'order', 'cluster_number', 'project', 'name',
                    'code',  'device_type',	'signal_type',
                    'io_address', 'location']

    # list_filter = [IOListFilter]
    list_filter = ('project', 'cluster_number', 'equipment_code', 'panel_number', 'Cluster')
    search_fields = (
        "name",
        "tag",
        "device_type"
    )

    resource_class = IOListResource




# admin.site.register(IOList)
admin.site.register(Project)
admin.site.register(Module)