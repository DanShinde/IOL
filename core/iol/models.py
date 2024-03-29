from django.db import models
from django.db.models.base import ModelBase
from django.contrib.auth.models import User
from django.db.models.signals import post_save

from django.dispatch import receiver



Segments=(('Carton/Tote Handling','Carton/Tote Handling'),
          ('Slit Roll','Slit Roll'),
          ('CBS', 'CBS'),
          ('Robotics','Robotics'),
          ('ASRS-MB','ASRS-MB'),
          ('ASRS-Stacker','ASRS-Stacker'))
ChoicesPLC=(('Siemens','Siemens'),
            ('Allen Bradley', 'Allen Bradley'),
            ('Mitsubishi', 'Mitsubishi'))
            

class Project(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(max_length=500, blank=True)
    segment = models.CharField(max_length=50, blank=True, default =Segments[0][0], choices = Segments)
    created_by = models.CharField(max_length=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField()
    is_Murr = models.BooleanField(default=False)
    isFreeze = models.BooleanField(default=False)
    PLC = models.CharField(max_length=50, default='Siemens', choices = ChoicesPLC)
    panels = models.JSONField(blank=True, null=True)
    panel_numbers = models.CharField(max_length=1000, blank=True, null=True)
    exported_at = models.DateTimeField( blank=True, null=True)
    exported_by = models.CharField(max_length=30, blank=True, null=True)

    # segment = models.CharField(max_length=50, blank=True, default =Segments[0][0], choices = Segments)

    def __str__(self):
        return self.name

class CountryManager(models.Manager):
    """Enable fixtures using self.sigla instead of `id`"""

    def get_by_natural_key(self, module):
        return self.get(module=module)

class Module(models.Model):
    module = models.CharField(max_length=50)
    description = models.TextField(max_length=500, blank=True)
    created_by = models.CharField(max_length=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    segment = models.CharField(max_length=50, blank=True, default =Segments[0][0], choices = Segments)
    def __str__(self):
        return self.module

class IOList(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    name = models.CharField(max_length=30)
    equipment_code = models.CharField(max_length=30)
    code = models.CharField(max_length=40)
    tag = models.CharField(max_length=100, editable=True)
    signal_type = models.CharField(max_length=10)
    device_type = models.TextField(max_length=100, blank=True)
    actual_description = models.TextField(max_length=200)
    panel_number = models.CharField(max_length=10, blank=True, null=True, default='CP01') #models.CharField(max_length=30, choices=[(k, k) for k in project.panel_keys]) 
    node = models.CharField(max_length=10, blank=True, null=True)
    rack = models.IntegerField(blank=True, null=True)
    module_position = models.IntegerField(blank=True, null=True)
    terminal_block = models.CharField(max_length=5, blank=True, null=True)
    terminal_number = models.IntegerField(blank=True, null=True)
    channel = models.IntegerField( blank=True, null=True)
    location = models.CharField(max_length=2, choices=(('FD', 'FD'), ('CP', 'CP')), default='CP')
    io_address = models.CharField(max_length=20, blank=True, null=True)
    Cluster = models.CharField(max_length=50, default="Testing")
    created_by = models.CharField(max_length=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    order = models.PositiveIntegerField(null=True)
    cluster_number = models.PositiveIntegerField(null=True)
    Demo_3d_Property = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.tag
    
    class Meta:
        ordering = ['order']


class Signals(models.Model):
    equipment_code = models.CharField(max_length=30)
    code = models.CharField(max_length=40)
    component_description = models.TextField(max_length=100, blank=True)
    function_purpose = models.TextField(max_length=100, blank=True)
    device_type = models.TextField(max_length=100, blank=True)
    signal_type = models.CharField(max_length=10, default="DI", choices=(('DI', 'DI'), ('DO', 'DO'), ('Encoder', 'Encoder')))
    remarks = models.TextField(max_length=100, blank=True)
    segment = models.CharField(max_length=50, blank=True,default=Segments[0][0], choices = Segments)
    initial_state = models.BooleanField(default=True)
    location = models.CharField(max_length=2, choices=(('FD', 'FD'), ('CP', 'CP')))
    module = models.ForeignKey(Module, on_delete=models.CASCADE,default= 1, related_name = "modules")
    created_by = models.CharField(max_length=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    Demo_3d_Property = models.CharField(max_length=200, blank=True, null=True)
    def __str__(self):
        if self.equipment_code != '':
            return f'{self.equipment_code}_{self.code}'
        else:
            return self.code

# @receiver(post_save, sender=Project)
# def create_profile(sender, instance, **kwargs):

class ProjectReport(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    updated_at = models.DateTimeField(blank=True, null=True)
    updated_by = models.CharField(max_length=50,blank=True, null=True)
    created_at = models.DateTimeField()
    created_by = models.CharField(max_length=50,blank=True, null=True)
    segment = models.CharField(max_length=50, blank=True, default =Segments[0][0], choices = Segments)

    def __str__(self):
        return str(self.project)


@receiver(post_save, sender=Project)
def create_project_report(sender, instance, created, **kwargs):
    if created:
        ProjectReport.objects.create(
            project=instance,
            created_at=instance.created_at,
            created_by=instance.created_by,
            segment = instance.segment,
            # You can set exported_at and exported_by based on your requirements
        )
