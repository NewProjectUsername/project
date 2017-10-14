from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Event)
admin.site.register(Lecture)
admin.site.register(Track)
admin.site.register(PaymentTicket)
admin.site.register(PaymentUPN)
admin.site.register(PaymentPayPal)
admin.site.register(EventCategory)