from django.contrib import admin
from .models import *
# Register your models here.
from iol.models import Signals, Module, IOList, Project
from import_export import resources
from import_export.admin import ImportMixin, ExportMixin, ImportExportMixin
from import_export.admin import ImportExportModelAdmin

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
        "device_type",
        "panel_number"
    )

    resource_class = IOListResource



class ProjectAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'description', 'segment','PLC', 'created_by','created_at', 'is_Murr']

admin.site.register(Project, ProjectAdmin)

class ModuleAdmin(admin.ModelAdmin):
    list_display = ['id', 'module', 'segment', 'created_by', 'created_at']

admin.site.register(Module, ModuleAdmin)

# class ReportAdmin(admin.ModelAdmin):
#     list_display = ['id', 'project','segment', 'created_by', 'created_at', 'updated_by', 'updated_at']





# class ReportAdmin(ImportExportModelAdmin):
#     list_display = ['id', 'project__name', 'segment', 'created_by', 'created_at', 'updated_by', 'updated_at']
#     # Define the export formats you want to enable
#     list_export = ('xlsx',)



class Reportresource(resources.ModelResource):
    class Meta:
        model = ProjectReport
        fields = ('id', 'project__name', 'segment', 'created_by', 'created_at', 'updated_by', 'updated_at')

class ReportExport(ImportExportModelAdmin):
    resource_class = Reportresource
    list_display = ['id', 'project', 'segment', 'created_by', 'created_at', 'updated_by', 'updated_at']
    ordering = ['-created_at']
    verbose_name = "Project Report"
    verbose_name_plural = "Project Reports"

admin.site.register(ProjectReport, ReportExport)

