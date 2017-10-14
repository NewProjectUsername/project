import pytz
from jsonfield import JSONField
from urllib.request import urlopen
import json

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.validators import MaxValueValidator, MinValueValidator
from django.conf import settings
from django.utils.crypto import get_random_string
#from django.contrib.auth.models import User
#from Landing.models import User
from django_countries.fields import CountryField
from django.contrib.auth import get_user_model

import Ideconference.settings as settings

from utils.models import Timestampable


# Create your models here.

UHF_DEVICE_POSITION = (
        ('L', _('Left')),
        ('R', _('Right'))
    )




class Event(Timestampable, models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='events')
    name = models.CharField(max_length=256)
    subdomain = models.CharField(max_length=32, unique=True)
    start_time = models.DateTimeField(blank=True)
    end_time = models.DateTimeField(blank=True)
    location = models.CharField(max_length=256)
    sent_mail = models.EmailField(max_length=70, null=True, blank=True)
    category = models.ForeignKey('EventCategory', null=True, blank=True)
    lat = models.FloatField(default=0)
    lng = models.FloatField(default=0)
    #username and password are for tracking purposes
    username = models.CharField(max_length=256, blank=True, null=True)
    password = models.CharField(max_length=256, blank=True, null=True)
    timezone = models.CharField(max_length=32, null=True, blank=True)

    first_step_info = models.TextField(max_length=20000, blank=True, null=True)

    participant_fields = JSONField(blank=True, null=True, default=["name", "surname"])
    participant_reqired_fields = JSONField(blank=True, null=True, default=["name", "surname"])

    companion_fields = JSONField(blank=True, null=True)
    companion_reqired_fields = JSONField(blank=True, null=True)

    payment_text = models.CharField(max_length=256, blank=True, null=True)

    payment_sent_mail_upn = models.TextField(max_length=5000, blank=True, null=True)
    payment_sent_mail_paypal = models.TextField(max_length=5000, blank=True, null=True)

    promotion_code = models.BooleanField(default=False)


    is_public = models.BooleanField(default=False)

    logo = models.ImageField(upload_to='media_cdn/logo/', max_length=1000, blank=True, null=True)
    public_logo = models.ImageField(upload_to='media_cdn/public_logo/', max_length=1000, blank=True, null=True)
    #added by Viktor, to check if user went through all the event adding steps
    #needed to distinguish whether user is editing or adding the event
    #add_finished = models.BooleanField(default=False)
    registration_step_finished = models.IntegerField(default=0)
    token = models.CharField(max_length=100, null=True, blank=True)
    api_username = models.CharField(max_length=32, null=True, blank=True)
    api_key = models.CharField(max_length=32, null=True, blank=True)
    calculated = models.BooleanField(default=False)
    registration_step_finished = models.IntegerField(default=0)
    #added by Viktor on 5.9.2017 in order to save ratios and card designer type
    card_designer = JSONField(blank=True, null=True)

    def __str__(self):
        """String representation ..."""

        return self.name

    def save(self, *args, **kwargs):
        self.sent_mail = self.subdomain + settings.EMAIL_DOMAIN
        '''
        url = 'https://maps.googleapis.com/maps/api/timezone/json?location=' + str(self.lat) + ',' + str(self.lng) + '&timestamp=1458000000&key=' + settings.GOOGLE_MAPS_TZ_API_KEY
        response = urlopen(url).read().decode('utf8')
        self.timezone = json.loads(response)['timeZoneId']'''
        if not self.api_key:
            self.api_key = self.subdomain[:3] + get_random_string(length=5)
            self.api_username = self.subdomain

        super(Event, self).save(*args, **kwargs)


class EventCategory(Timestampable, models.Model):
    title = models.CharField(max_length=256, blank=True, null=True)

    def __str__(self):
        return self.title


class Payment(Timestampable, models.Model):
    event = models.ForeignKey('Event', related_name='payment')

    def get_payments(self):
        payments = {}
        if PaymentUPN.objects.filter(payment_ptr=self.id):
            return ('UPN', PaymentUPN.objects.get(payment_ptr=self.id))
        if PaymentPayPal.objects.filter(payment_ptr=self.id):
            return ('PayPal', PaymentPayPal.objects.get(payment_ptr=self.id))


class PaymentUPN(Payment):
    upn_enabled = models.BooleanField(default=False)
    name = models.CharField(max_length=512, blank=True, null=True)
    address = models.CharField(max_length=512, blank=True, null=True)
    account_number = models.CharField(max_length=512, blank=True, null=True)
    bic = models.CharField(max_length=512, blank=True, null=True)

    def __str__(self):
        """String representation ..."""
        return self.event.name


class PaymentPayPal(Payment):
    paypal_enabled = models.BooleanField(default=False)
    client_id = models.CharField(max_length=512, blank=True, null=True)
    client_key = models.CharField(max_length=512, blank=True, null=True)
    mode = models.CharField(max_length=512, blank=True, null=True)

    def __str__(self):
        """String representation ..."""
        return self.event.name


class PaymentTicket(Timestampable, models.Model):
    event = models.ForeignKey('Event', related_name='tickets')
    free = models.BooleanField(default=False)
    payable = models.BooleanField(default=False)
    ticket_name = models.CharField(max_length=512, blank=True, null=True)
    days = models.CharField(max_length=32, blank=True, null=True)
    price = models.FloatField(default=0.0)
    track = models.ForeignKey('Track',
                              blank=True,
                              null=True,
                              related_name="track")

    def __str__(self):
        """String representation ..."""
        return self.event.name


class Lecture(Timestampable, models.Model):
    event = models.ForeignKey("Event")
    name = models.CharField(max_length=256)
    track = models.ForeignKey("Track", blank=True, null=True, default=None)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    device_id = models.CharField(max_length=256, blank=True, null=True)
    device_id2 = models.CharField(max_length=256, blank=True, null=True)
    lecture_room = models.CharField(_('Lecture room'), max_length=256, blank=True, null=True)
    bar_tracking = models.BooleanField(default=False)
    uhf_tracking = models.BooleanField(default=False)
    access_control = models.BooleanField(default=False)
    device_entrance_position = models.CharField(_('UHF Device ID 1 position'), max_length=1, choices=UHF_DEVICE_POSITION, default='R')
    device_entrance_position2 = models.CharField(_('UHF Device ID 2 position'), max_length=1, choices=UHF_DEVICE_POSITION, default='R')

    def __str__(self):
        return self.name


class Track(models.Model):
    """Model that holds tracks for each event. Very basic stuff,
    but implements nicely into modelform. wup wup."""
    event = models.ForeignKey("Event")
    name = models.CharField(max_length=256, blank=False, null=True)
    track_is_payable = models.BooleanField('is payable', default=False)

    def __str__(self):
        return self.name
