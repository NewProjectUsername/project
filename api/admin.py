from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from api.models import UhfTime
# Register your models here.

class UhfTimeResource(resources.ModelResource):
    class Meta:
        model = UhfTime
        export_order = ('user__name','user__surname','direction', 'time_of_sec', 'lecture__name')
        fields = ('user__name','user__surname','direction', 'time_of_sec', 'lecture__name')

class UhfTimeAdmin(ImportExportModelAdmin):
    resource_class = UhfTimeResource
    ordering = ('time_of_sec',) # The negative sign indicate descendent order
    search_fields = ['user__name','user__surname','user__barcode_no']
    list_display = ('user', 'direction', 'time_of_sec', 'lecture')
    list_filter = ['lecture', ]
    

admin.site.register(UhfTime, UhfTimeAdmin)