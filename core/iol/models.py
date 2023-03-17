from django.db import models
from django.db.models.base import ModelBase


class Project(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(max_length=500, blank=True)

    def __str__(self):
        return self.name

class CountryManager(models.Manager):
    """Enable fixtures using self.sigla instead of `id`"""

    def get_by_natural_key(self, module):
        return self.get(module=module)

class Module(models.Model):
    module = models.CharField(max_length=50)
    def __str__(self):
        return self.module

class IOList(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    name = models.CharField(max_length=30)
    equipment_code = models.CharField(max_length=30)
    code = models.CharField(max_length=40)
    tag = models.CharField(max_length=100, editable=False)
    signal_type = models.CharField(max_length=10)
    device_type = models.TextField(max_length=100, blank=True)
    actual_description = models.TextField(max_length=100)
    panel_number = models.CharField(max_length=10, blank=True, null=True, default='CP01')
    node = models.CharField(max_length=10, blank=True, null=True)
    rack = models.IntegerField(blank=True, null=True)
    module_position = models.IntegerField(blank=True, null=True)
    terminal_block = models.CharField(max_length=5, blank=True, null=True)
    terminal_number = models.IntegerField(blank=True, null=True)
    channel = models.IntegerField( blank=True, null=True)
    location = models.CharField(max_length=2, choices=(('FD', 'FD'), ('CP', 'CP')), default='CP')
    io_address = models.CharField(max_length=10, blank=True, null=True)
    module = models.CharField(max_length=50, default="Testing")
    def __str__(self):
        return self.tag


class Signals(models.Model):
    equipment_code = models.CharField(max_length=30)
    code = models.CharField(max_length=40)
    component_description = models.TextField(max_length=100, blank=True)
    function_purpose = models.TextField(max_length=100, blank=True)
    device_type = models.TextField(max_length=100, blank=True)
    signal_type = models.CharField(max_length=10, default="DI", choices=(('DI', 'DI'), ('DO', 'DO'), ('Encoder', 'Encoder')))
    remarks = models.TextField(max_length=100, blank=True)
    segment = models.CharField(max_length=50, blank=True, choices=(('Carton/Tote Handling','Slit Roll'),('Carton/Tote Handling','Slit Roll')))
    initial_state = models.BooleanField(default=True)
    location = models.CharField(max_length=2, choices=(('FD', 'FD'), ('CP', 'CP')))
    module = models.ForeignKey(Module, on_delete=models.CASCADE,default= 1, related_name = "modules")
    def __str__(self):
        return f'{self.equipment_code}_{self.code}'





