from django.db import models
from django.db.models.base import ModelBase


class Project(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(max_length=500, blank=True)

    def __str__(self):
        return self.name

class IOList(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    name = models.CharField(max_length=30)
    equipment_code = models.CharField(max_length=30)
    code = models.CharField(max_length=40)
    tag = models.CharField(max_length=100, editable=False)
    signal_type = models.CharField(max_length=10)
    actual_description = models.TextField(max_length=100)
    panel_number = models.CharField(max_length=10, blank=True, null=True)
    node = models.CharField(max_length=10, blank=True, null=True)
    rack = models.IntegerField(blank=True, null=True)
    module_position = models.IntegerField(blank=True, null=True)
    terminal_block = models.CharField(max_length=5, blank=True, null=True)
    terminal_number = models.IntegerField(blank=True, null=True)
    channel = models.IntegerField( blank=True, null=True)
    io_address = models.CharField(max_length=10, blank=True, null=True)
    modules = models.ManyToManyField('Module', verbose_name='modules')


class Module(models.Model):
    module = models.CharField(max_length=50)


class Signals(models.Model):
    equipment_code = models.CharField(max_length=30)
    code = models.CharField(max_length=40)
    component_description = models.TextField(max_length=100, blank=True)
    function_purpose = models.TextField(max_length=100, blank=True)
    device_type = models.TextField(max_length=100, blank=True)
    signal_type = models.CharField(max_length=10, default="DI", choices=(('DI', 'DI'), ('DO', 'DO'), ('Encoder', 'Encoder')))
    remarks = models.TextField(max_length=100, blank=True)
    segment = models.CharField(max_length=50, blank=True)
    initial_state = models.BooleanField(default=True)
    location = models.CharField(max_length=2, choices=(('FD', 'FD'), ('CP', 'CP')))
    module = models.ManyToManyField(Module, verbose_name='modules')

    def __str__(self):
        return self.equipment_code+"_"+self.code
    





