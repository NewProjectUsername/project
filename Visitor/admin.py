from django.contrib import admin
from django.contrib.auth import get_user_model
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from .models import *

class EventProfileResource(resources.ModelResource):
    class Meta:
        model = EventProfile
        fields = ('name','surname','barcode_no')

class EventProfileAdmin(ImportExportModelAdmin):
    resource_class = EventProfileResource
    ordering = ('name',) # The negative sign indicate descendent order
    search_fields = ['name','surname','barcode_no']
    list_display = ('name','surname','barcode_no')
    list_filter = ('name', 'surname')




# Register your models here.
admin.site.register(Profile)
admin.site.register(EventProfile, EventProfileAdmin)