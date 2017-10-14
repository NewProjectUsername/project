import pytz
import json
from urllib.request import urlopen

from django import forms
from django.forms import (ModelForm, Form, ModelMultipleChoiceField, CharField,
                          TextInput, PasswordInput, CheckboxSelectMultiple,
                          FileField, modelformset_factory)
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext as _

from django_summernote.widgets import SummernoteWidget, SummernoteInplaceWidget
from bootstrap3_datetime.widgets import DateTimePicker

from Visitor.models import EventProfile

from .models import (Event, Lecture, Track, PaymentUPN, PaymentPayPal,
                     PaymentTicket)


User = get_user_model()

class EventAuthForm(AuthenticationForm):
    username = CharField(label="Username", widget=TextInput(attrs={'class': 'form-control','placeholder': 'Username', 'type': 'text'}))
    password = CharField(label="Password", widget=PasswordInput(attrs={'class': 'form-password form-control','placeholder':'Password', 'type': 'password'}))


class EventForm(ModelForm):
    class Meta:
        model = Event
        #2017-06-08 12:00:00 location field removed
        fields = ['name', 'subdomain', 'sent_mail', 'category', 'start_time', 'end_time', 'is_public', 'logo', 'public_logo','api_username','api_key','location', 'lng', 'lat']

        labels = {'is_public': _('Event visible on mail page')}
        widgets = {
            'start_time': DateTimePicker(options={'locale': settings.LANGUAGE_CODE[:2]}, format='%d. %m. %Y %H:%M'),#, attrs={'input_formats': settings.DATETIME_FORMATS}),
            'end_time': DateTimePicker(options={'locale': settings.LANGUAGE_CODE[:2]}, format='%d. %m. %Y %H:%M'),#, attrs={'input_formats': settings.DATETIME_FORMATS}),
        }

    def __init__(self, *args, **kwargs):
        _instance = kwargs.get('instance', False)
        if _instance:
            initial = kwargs.get('initial', {})
            event_timezone = pytz.timezone(_instance.timezone)

            initial['start_time'] = _instance.start_time.astimezone(event_timezone).replace(tzinfo=None)
            initial['end_time'] = _instance.end_time.astimezone(event_timezone).replace(tzinfo=None)

            kwargs['initial'] = initial
        super(EventForm, self).__init__(*args, **kwargs)
        self.fields['sent_mail'].widget.attrs['readonly'] = True
        # alredy added attribute as readonly in html template event_data
        self.fields['api_username'].widget.attrs['readonly'] = True
        self.fields['api_key'].widget.attrs['readonly'] = True
        self.fields['location'].widget.attrs['onFocus'] = "geolocate()"
        self.fields['lat'].widget = forms.HiddenInput()
        self.fields['lng'].widget = forms.HiddenInput()
        self.fields['start_time'].required = True
        self.fields['end_time'].required = True

    def fix_time_range(self, start, end):
        """Fix available datetimeranges, after the form has been created."""
        start = str(start)
        end = str(end)
        dtpatt = {
            'locale': settings.LANGUAGE_CODE[:2],
            'maxDate': end,
            'minDate': start,
            'useCurrent': False
        }

        self.fields['start_time'].widget.options.update(dtpatt)
        self.fields['end_time'].widget.options.update(dtpatt)

    def clean(self):
        """Override the clean method to check if start and end date come in succession."""
        data = super(EventForm, self).clean()
        start = data.get('start_time')
        end = data.get('end_time')

        msg = _('Start date must come before end date.')


        if start and end:
            if start >= end:
                print('here 2')
                self.add_error('start_time', msg)
                self.add_error('end_time', msg)

        url = 'https://maps.googleapis.com/maps/api/timezone/json?location=' + str(self.data['lat']) + ',' + str(self.data['lng']) + '&timestamp=1458000000&key=' + settings.GOOGLE_MAPS_TZ_API_KEY
        response = urlopen(url).read().decode('utf8')
        timezone = json.loads(response)['timeZoneId']

        self.requested_timezone = timezone
        # print(timezone)

        # -- Save time with regards to the chosen time zone, not the browser-detected timezone.
        tz = pytz.timezone(self.requested_timezone)
        data['start_time'] = tz.localize(start.replace(tzinfo=None))
        data['end_time'] = tz.localize(end.replace(tzinfo=None))

        return data

    def save(self, commit=True):
        obj = super(EventForm, self).save(commit=commit)

        obj.timezone = self.requested_timezone


        return obj


class EventFirstStep(ModelForm):
    class Meta:
        model = Event
        fields = ['first_step_info']
        widgets = {
            'first_step_info': SummernoteWidget(attrs={'width': '100%'})
        }


class EventLectures(ModelForm):

    def __init__(self, event, *args, **kwargs):
        """Overwriting modelform constructor. Event must be passed in on
        instantiation, so that existing tracks can be listed."""
        _instance = kwargs.get('instance', False)
        if _instance:
            initial = kwargs.get('initial', {})
            event_timezone = pytz.timezone(event.timezone)

            initial['start_time'] = _instance.start_time.astimezone(event_timezone).replace(tzinfo=None)
            initial['end_time'] = _instance.end_time.astimezone(event_timezone).replace(tzinfo=None)

            kwargs['initial'] = initial

        super(EventLectures, self).__init__(*args, **kwargs)

        self.event = event
        self.fields['track'] = forms.ModelChoiceField(
            queryset=Track.objects.filter(event=event),
            required=False
        )

    class Meta:
        model = Lecture
        fields = ['name', 'start_time', 'end_time', 'device_id', 'device_id2', 'lecture_room', 'bar_tracking', 'uhf_tracking', 'access_control', 'device_entrance_position', 'device_entrance_position2', 'track']
        widgets = {
            'start_time': DateTimePicker(options={'locale': settings.LANGUAGE_CODE[:2]}, format='%d. %m. %Y %H:%M'),#,'format': 'MM/DD/YYYY HH:mm'}),
            'end_time': DateTimePicker(options={'locale': settings.LANGUAGE_CODE[:2]}, format='%d. %m. %Y %H:%M')#,'format': 'MM/DD/YYYY HH:mm'})
        }

    def fix_time_range(self, start, end):
        """Fix available datetimeranges, after the form has been created."""
        start = str(start)
        end = str(end)

        event_timezone = pytz.timezone(self.event.timezone)

        options_start = {
            'maxDate': end, 'minDate': start, 'locale': settings.LANGUAGE_CODE[:2], 'useCurrent': False,
            'defaultDate': str(self.event.start_time.astimezone(event_timezone).replace(tzinfo=None))
            }

        options_end = {
            'maxDate': end, 'minDate': start, 'locale': settings.LANGUAGE_CODE[:2], 'useCurrent': False,
            'defaultDate': str(self.event.end_time.astimezone(event_timezone).replace(tzinfo=None))
            }

        self.fields['start_time'].widget.options.update(options_start)
        self.fields['end_time'].widget.options.update(options_end)


    def clean(self):
        """Override the clean method to check if start and end date come in succession."""
        cleaned_data = super(EventLectures, self).clean()

        start = cleaned_data.get('start_time')
        end = cleaned_data.get('end_time')

        tz = pytz.timezone(self.event.timezone)
        start_time = tz.localize(start.replace(tzinfo=None))
        end_time = tz.localize(end.replace(tzinfo=None))

        if start_time and end_time:
            msg = _('Start date must come before end date.')
            if start_time >= end_time:
                self.add_error('start_time', msg)
                self.add_error('end_time', msg)


            msg = _('Lecture dates must be within the event dates.')
            if not (self.instance.pk is None):
                if start_time < self.instance.start_time:
                    self.add_error('start_time', msg)
                if end_time > self.instance.end_time:
                    self.add_error('end_time', msg)

        cleaned_data['start_time'] = start_time
        cleaned_data['end_time'] = end_time

        return cleaned_data


class EventTracks(ModelForm):
    """Form for adding tracks to a specific (!!) event."""
    def __init__(self, event, *args, **kwargs):
        super(EventTracks, self).__init__(*args, **kwargs)
        self.event = event

    def clean(self):
        """Override the clean method to validate the string."""
        cleaned_data = super(EventTracks, self).clean()
        name = cleaned_data.get('name')

        msg = _('Track name must be 3 characters or longer')

        if len(name) < 3:
            self.add_error('name', msg)

        msg = _('Track by that name already exists for this event.')
        count = Track.objects.filter(name=name, event=self.event).count()

        if count > 0:
            self.add_error('name', msg)


    class Meta:
        model = Track
        exclude = ['event', ]

class EventUsersIDs(ModelForm):
    """Takes care of entering users IDs.
    (after the users have already registered)"""

    class Meta:
        model = EventProfile

        fields = ['idnumber']

class GenericFileUploadForm(Form):
    file = FileField()

    def __init__(self, *args, **kwargs):
        super(GenericFileUploadForm, self).__init__(*args, **kwargs)
        self.fields['file'].label = _('File with user IDs')

class ParticipantFields(ModelForm):

    def __init__(self, *args, required_fields=[], **kwargs):
        """Sets the required fields after the form has
        been instantiated."""
        super(ParticipantFields, self).__init__(*args, **kwargs)

        for key in required_fields:
            self.fields[key].required = True

        #self.fields['name'].required = True
        #self.fields['surname'].required = True

    class Meta:
        model = EventProfile
        fields = ['name', 'surname', 'gender', 'address', 'city', 'post',
                  'country', 'birth_year', 'status', 'days_on_event', 'dinner',
                  'nutrition', 'company_address', 'company_invoice', 'company_name',
                  'email', 'tax_number', 'company_email', 'network_visible']
        labels = {
            'name': _('name'),
            'surname': _('surname'),
            'email': _('email'),
            'gender': _('gender'),
            'address': _('address'),
            'city': _('city'),
            'post': _('post'),
            'country': _('Country'),
            'birth_year': _('Birth year'),
            'status': _('Status of attendees'),
            'days_on_event': _('days of event'),
            'nutrition': _('Special nutrition options'),
            'dinner': _('Dinner'),
            'company_invoice': _('Invoice on company'),
            'company_name': _('Company name'),
            'company_address': _('address'),
            'tax_number': _('Tax no'),
            'company_email': _('Company email / telephone'),
            'network_visible': _('Visible in network tab'),


        }
        widgets = {
            'birth_year': DateTimePicker(options={'locale': settings.LANGUAGE_CODE[:2], 'viewMode': 'years'}, format='%d. %m. %Y')#, 'format': settings.BIRTH_YEAR_FORMAT})
        }

    def clean(self):
        data = super(ParticipantFields, self).clean()

        birth_year = data.get('birth_year')

        if birth_year:
            birth_year = self.cleaned_data['birth_year']
            data['birth_year'] = pytz.utc.localize(birth_year.replace(tzinfo=None))

        return data


class ParticipantSoft(ModelForm):

    def __init__(self, *args, required_fields=[], **kwargs):
        """Sets the required fields after the form has
        been instantiated."""
        super(ParticipantSoft, self).__init__(*args, **kwargs)

        self.fields['name'].required = True
        self.fields['surname'].required = True

    class Meta:
        model = EventProfile
        fields = ['name', 'surname', 'company_name', 'uhf_id', 'note']
        labels = {
            'name': _('Name'),
            'surname': _('Surname'),
            'company_name': _('Company name'),
            'uhf_id': _('UHF ID'),
            'note': _('Note')
        }
        required = ['name', 'surname']

class ParticipantUpdate(ModelForm):

    class Meta:
        model = EventProfile
        fields = ['uhf_id', 'note', 'payed']
        labels = {
            'uhf_id': _('UHF ID'),
            'note': _('Note'),
            'payed': _('Payment status')
        }

class CompanionFields(ModelForm):

    def __init__(self, *args, required_fields=[], **kwargs):
        """Sets the required fields after the form has
        been instantiated."""
        super(CompanionFields, self).__init__(*args, **kwargs)

        for key in required_fields:
            self.fields[key].required = True

    class Meta:
        model = EventProfile
        fields = ['name', 'surname', 'gender', 'address', 'city', 'post',
                  'country', 'birth_year', 'status', 'days_on_event', 'dinner', 'nutrition']


        labels = {
            'name': _('Name'),
            'surname': _('Surname'),
            'gender': _('Gender'),
            'address': _('Address'),
            'city': _('City'),
            'post': _('Post'),
            'country': _('Country'),
            'birth_year': _('Birth year'),
            'nutrition': _('Special nutrition options'),
            'dinner': _('Dinner'),
            'status': _('Status of attendees'),
            'days_on_event': _('Days on event')
        }
        widgets = {
            'birth_year': DateTimePicker(options={'locale': settings.LANGUAGE_CODE, 'format': settings.BIRTH_YEAR_FORMAT,
                                                  'viewMode': 'years'})
        }

class EventPayment(ModelForm):
    class Meta:
        model = Event
        fields = ['payment_text', 'payment_sent_mail_upn', 'payment_sent_mail_paypal', 'promotion_code']
        widgets = {
            'payment_text': SummernoteWidget(attrs={'width': '100%'}),
            'payment_sent_mail_upn': SummernoteWidget(attrs={'width': '100%'}),
            'payment_sent_mail_paypal': SummernoteWidget(attrs={'width': '100%'}),
        }


class PaymentUPNForm(ModelForm):
    class Meta:
        model = PaymentUPN
        exclude = ['event', 'upn_enabled', ]
        labels = {
            'account_number': _('IBAN'),
            'bic': _('BIC'),
        },
        widgets = {
            "name": forms.TextInput(attrs={'class': 'form-control payment-test pad-test'}),
            "address": forms.TextInput(attrs={'class': 'form-control payment-test'}),
            "account_number": forms.TextInput(attrs={'class': 'form-control payment-test pad-test'}),
            "bic": forms.TextInput(attrs={'class': 'form-control payment-test'}),
        }


class PaymentPayPalForm(ModelForm):
    class Meta:
        model = PaymentPayPal
        exclude = ['event', 'paypal_enabled']
        widgets = {
            "client_id": forms.TextInput(attrs={'class': 'form-control payment-test pad-test'}),
            "client_key": forms.TextInput(attrs={'class': 'form-control payment-test'}),
            "mode": forms.TextInput(attrs={'class': 'form-control payment-test pad-test'}),
        }


def getPaymentFormSet(choices):
    paymentTicketFormSet = modelformset_factory(PaymentTicket,
                                                exclude=['event', 'dinner', 'track'],
                                                widgets={'free': forms.CheckboxInput(attrs={'class': 'payment-test-free sub-check'}),
                                                         'payable': forms.CheckboxInput(attrs={'class': 'payment-test-payable sub-chek'}),
                                                         'ticket_name': forms.TextInput(attrs={'class': 'payment-test-name'}),
                                                         'days': forms.Select(choices=choices,attrs={'class': 'payment-test-day'}),
                                                         'price': forms.TextInput(attrs={'class': 'payment-test-price pay-price'}),
                                                         },
                                                labels={'free': _('Free Event'),
                                                        'days': _('Payable Event'),
                                                        'ticket_name':_('Ticket Name'),
                                                        'participant_status': _('Name of registration fee'),
                                                        'days': _('Type of registration')
                                                        },
                                                can_delete=True)
    return paymentTicketFormSet
