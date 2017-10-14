import csv
from io import StringIO
import pytz
from datetime import datetime
import json
from datetime import timedelta

from django.http import HttpResponse, HttpResponseForbidden, Http404
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required, permission_required
from django.utils import timezone
from django.utils.translation import ugettext as _
from django.http import JsonResponse

import Event.utils as utils
from Visitor.models import EventProfile, Profile

from .models import Event, Lecture, PaymentTicket, PaymentPayPal, PaymentUPN, Track
from .forms import (EventAuthForm, EventForm, EventFirstStep, EventLectures,
                    GenericFileUploadForm, EventUsersIDs, EventTracks,
                    ParticipantFields, CompanionFields,
                    EventPayment, PaymentUPNForm, PaymentPayPalForm,
                    getPaymentFormSet, ParticipantSoft, getPaymentFormSet, ParticipantUpdate)
from api.models import UhfTime


User = get_user_model()

# Create your views here.
#first step
@login_required
@permission_required('Event.add_event')
def add_event(request, event_name=None):
    context = {}
    if event_name:
        event_instance = utils.get_event_by_name(request, event_name)
        context['event'] = event_instance
        if (event_instance.registration_step_finished < 1):
            event_instance.registration_step_finished = 1
            event_instance.save()                
    else:
        event_instance = None
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event_instance)
        if form.is_valid():
            #we are only updating event
            if event_name:
                event_instance.save()
                #if user has not finished all the steps, he still uses the button "Save and go to the next"
                if (event_instance.registration_step_finished < 7):
                    return redirect('add_event_description', event_name=event_instance.subdomain)
                #if user has finished registration, he is redirected to the same page, suing button "Save"
                else:
                    return redirect('modify_event', event_name=event_instance.subdomain)
            else:
                #we are adding the event
                new_event = form.save(commit=False)
                new_event.user = request.user
                new_event.registration_step_finished = 1
                new_event.save()
                return redirect('add_event_description', event_name=new_event.subdomain)
        else:
            context['form'] = form
    else:
        context['form'] = EventForm(instance=event_instance)
        context['form'].fix_time_range(datetime.now(),
                                       datetime.now()+timedelta(days=1000))
        context['maps'] = settings.GOOGLE_MAPS_API_KEY
    
    return render(request, 'Event/event_data.html', context)

#second step
@login_required
def add_event_description(request, event_name=None):
    """Add/edit event description (wysiwyg editor)."""
    context = {}
    event_instance = utils.get_event_by_name(request, event_name)
    form = EventFirstStep(instance=event_instance)
    if (event_instance.registration_step_finished < 2):
        event_instance.registration_step_finished = 2
        event_instance.save()  
    if request.method == 'POST':
        
        form = EventFirstStep(request.POST, instance=event_instance)
        if form.is_valid():
            form.save()
            if event_instance.registration_step_finished == 7:
                return redirect('add_event_description', event_name=event_name)
            else:
                return redirect('add_event_participants', event_name=event_name)

    context['form'] = form
    context['event'] = event_instance
    return render(request, 'Event/event_description.html', context)

@login_required
def add_event_lectures(request, event_name, lecture_id=False, download=False, add_track=False):
    """Add new lectures and show existing ones."""
    context = {}

    event_instance = utils.get_event_by_name(request, event_name)
    event_timezone = pytz.timezone(event_instance.timezone)
    context['event'] = event_instance

    if (event_instance.registration_step_finished < 5):
        event_instance.registration_step_finished = 5;
        event_instance.save()


    if download:
        # -- Send the .csv file to the user.
        lectures = Lecture.objects.filter(event=event_instance).order_by('-pk')
        response = utils.csv_lecture_file(event_instance, lectures)

        return response

    elif add_track:
        tracks_form = EventTracks(event_instance, request.POST or None)
        if request.method == 'POST':
            if tracks_form.is_valid():
                new_track = tracks_form.save(commit=False)
                new_track.event = event_instance
                new_track.save()
                messages.success(request, "Track added!",extra_tags="tracks")
                tracks_form = EventTracks(event_instance)
        
        form = EventLectures(event_instance)
        print('iz_baze', event_instance.start_time)
        print('s timez', event_instance.start_time.astimezone(event_timezone))
        form.fix_time_range(event_instance.start_time.astimezone(event_timezone), event_instance.end_time)
        context['form'] = form
        context['tracks_form'] = tracks_form

        context['file_form'] = GenericFileUploadForm()
        context['lectures'] = Lecture.objects.filter(event=event_instance).order_by('-pk')

        return render(request, 'Event/event_lectures.html', context)

    elif request.FILES:
        # -- Receive the uploaded file.
        file_form = utils.handle_lectures_csv_file_upload(event_instance, request.FILES['file'])
        context['file_form'] = file_form
        form = EventLectures(event_instance)
        form.fix_time_range(event_instance.start_time, event_instance.end_time)
        context['form'] = form
        context['tracks_form'] = EventTracks(event_instance)
        context['lectures'] = Lecture.objects.filter(event=event_instance).order_by('-pk')

        return render(request, 'Event/event_lectures.html', context)

    else:
        # -- Process form data -- manually added lecture.
        context['file_form'] = GenericFileUploadForm()
        context['lectures'] = Lecture.objects.filter(event=event_instance).order_by('-pk')

        form = EventLectures(event_instance, request.POST or None)
        if request.method == 'POST':
            if form.is_valid():
                new_lecture = form.save(commit=False)
                new_lecture.event = event_instance
                new_lecture.save()
                messages.success(request, "lectures added",extra_tags="add")

                form = EventLectures(event_instance)

        tracks_form = EventTracks(event_instance)
        print('iz_baze', event_instance.start_time)
        print('s timez', event_instance.start_time.astimezone(event_timezone))
        print('s timez none', event_instance.start_time.astimezone(event_timezone).replace(tzinfo=None))
        form.fix_time_range(event_instance.start_time.astimezone(event_timezone).replace(tzinfo=None), event_instance.end_time.astimezone(event_timezone).replace(tzinfo=None))
        context['form'] = form
        context['tracks_form'] = tracks_form
        return render(request, 'Event/event_lectures.html', context)

@login_required
def modify_event_lecture(request, event_name, lecture_id):
    """Modify existing lecture."""
    context = {}
    event_instance = utils.get_event_by_name(request, event_name)
    context['event'] = event_instance

    lecture_instance = get_object_or_404(Lecture, pk=lecture_id)


    form = EventLectures(event_instance, request.POST or None, instance=lecture_instance)
    if request.method == 'POST':
        if form.is_valid():
            new_lecture = form.save(commit=False)
            new_lecture.event = event_instance
            new_lecture.save()

            return redirect('add_event_lectures', event_name=event_name)

    # -- Bug. Fixing time corrupts instance.
    form.fix_time_range(event_instance.start_time, event_instance.end_time)
    context['form'] = form
    context['lecture_id'] = lecture_id

    return render(request, 'Event/event_lectures_modify.html', context)


@login_required
def remove_event_lecture(request, event_name, lecture_id):
    """Deletes lecture and redirects."""
    event_instance = utils.get_event_by_name(request, event_name)

    query = Lecture.objects.get(pk=lecture_id)
    query.delete()

    return redirect('add_event_lectures', event_name=event_name)


@login_required
def list_events(request):
    """Add new event and show existing ones."""
    user = request.user
    all_events = Event.objects.filter(user=user)
    current_date = datetime.now()
    events_in_progress = all_events.filter(user=user, start_time__lte=current_date, end_time__gte=current_date)
    enames= []
    [enames.append(event_obj.name) for event_obj in events_in_progress]
    context = dict(events=all_events,
                   eventor=user,
                   events_in_progress=events_in_progress,
                   pevent_name = enames,)
    return render(request, 'Event/event_list.html', context)


def event_details(request, id):
    """Dummy function"""
    idInt = int(id)
    event = Event.objects.get(id=idInt)
    resp = event.name
    return HttpResponse(resp)

@login_required
def event_users_data(request, event_name, payed='all'):
    """List users registered with the particular event. User list
    download and upload with IDs."""
    event_instance = utils.get_event_by_name(request, event_name)
    context = dict()
    context['event'] = event_instance

    # -- Determine which of the required fields are in EventProfile.
    event_instance.participant_fields.append('payed')
    event_instance.participant_fields.append('id')
    event_instance.participant_fields.append('user')
    event_instance.participant_fields.append('upn_reference')
    selected_fields = tuple(event_instance.participant_fields)
    

    if request.FILES:
        # -- Receive the uploaded file.
        id_form = utils.handle_id_csv_file_upload(event_instance, request.FILES['file'])
        context['id_form'] = id_form
    elif request.POST and ('participant' in request.POST):
        EventProfile.objects.filter(id__in=request.POST.getlist('participant')).delete()
    else:
        context['id_form'] = GenericFileUploadForm()
    
    # -- Filter participants based on payed status.
    participants = EventProfile.objects.values(*selected_fields).filter(event=event_instance, is_companion=False)
    payed_count = participants.filter(payed=True).count()
    unpayed_count = participants.filter(payed=False).count()
    if 'all' == payed:
        pass
    elif 'payed' == payed:
        pass                       
    elif 'not-payed' == payed:
        pass
    else:
        raise Http404('Filter option does not exist.')

    context['unpayedcount'] = unpayed_count
    context['payedcount'] = payed_count
    context['payed'] = payed
    context['payedcount'] = payed_count
    context['unpayedcount'] = unpayed_count
    context['participants'] = participants
    context['selected_fields'] = selected_fields



    return render(request, 'Event/event_users_data.html', context)

@login_required
def download_event_users_data(request, event_name, payed='all'):
    """Send user list without IDs to event admin."""
    event_instance = utils.get_event_by_name(request, event_name)

    # -- Filter participants based on payed status.
    if 'all' == payed:
        participants = EventProfile.objects.select_related('user').filter(event=event_instance,
                                                   is_companion=False)
    elif 'payed' == payed:
        participants = EventProfile.objects.select_related('user').filter(event=event_instance,
                                                   payed=True, is_companion=False)
    elif 'not-payed' == payed:
        participants = EventProfile.objects.select_related('user').filter(event=event_instance,
                                                   payed=False, is_companion=False)
    else:
        raise Http404('Filter option does not exist.')

    return utils.csv_participants_file(participants, event_instance.participant_fields)


@login_required
def download_event_users_upn_references(request, event_name):
    """Sends a csv export with name, surname and upn_reference for users,
    that have upn type of payment."""
    event_instance = utils.get_event_by_name(request, event_name)


    return utils.upn_references_csv_export(event_instance)

#3th step
@login_required
def event_participants(request, event_name):
    """Step two participant information"""
    event_instance = utils.get_event_by_name(request, event_name)
    if (event_instance.registration_step_finished < 3):
        event_instance.registration_step_finished = 3   
        event_instance.save()
    context = dict(participant_form_error=False)
    if request.method == 'POST':
        form = request.POST.getlist('form')
        required = request.POST.getlist('required')
        if form and ('name' in form) and ('surname' in required):
            event = Event.objects.filter(subdomain=event_name).update(participant_fields=form,
                                                                      participant_reqired_fields=required)
            if event_instance.registration_step_finished == 7:
                return redirect('add_event_participants', event_name=event_name)
            else: 
                return redirect('add_event_companion', event_name=event_name)

            return redirect('add_event_companion', event_name=event_name)
        else:
            context['participant_form_error'] = True
            
    participant_form = ParticipantFields(instance=event_instance)
    context['fields_personal'] = [(key, participant_form.fields[key].label, participant_form.fields[key].__class__.__name__) for key in participant_form.fields
                                        if key in settings.VISITOR_FIELD_CLASS['personal']]
    context['fields_company'] = [(key, participant_form.fields[key].label, participant_form.fields[key].__class__.__name__) for key in participant_form.fields
                                        if key in settings.VISITOR_FIELD_CLASS['company']]
    context['fields_event'] = [(key, participant_form.fields[key].label, participant_form.fields[key].__class__.__name__) for key in participant_form.fields
                                        if key in settings.VISITOR_FIELD_CLASS['event']]
    context['event'] = event_instance

    return render(request, 'Event/event_participants.html', context)

#4th step
@login_required
def event_companion(request, event_name):
    """Step four companion information"""
    event_instance = utils.get_event_by_name(request, event_name)
    if (event_instance.registration_step_finished < 4):
        event_instance.registration_step_finished = 4
        event_instance.save()
    context = {}
    if request.method == 'POST':
        form = request.POST.getlist('form')
        required = request.POST.getlist('required')
        if form:
            event = Event.objects.filter(subdomain=event_name).update(companion_fields=form,
                                                                      companion_reqired_fields=required)
            if event_instance.registration_step_finished == 7:
                return redirect('add_event_companion', event_name=event_name)
            else:
                return redirect('add_event_lectures', event_name=event_name)
        else:
            return redirect('add_event_lectures', event_name=event_name)

    form = CompanionFields(instance=event_instance)
    context['fields_personal'] = [(key, form.fields[key].label, form.fields[key].__class__.__name__)
                                  for key in form.fields
                                  if key in settings.VISITOR_FIELD_CLASS['personal']]
    context['fields_company'] = [(key, form.fields[key].label, form.fields[key].__class__.__name__)
                                 for key in form.fields
                                 if key in settings.VISITOR_FIELD_CLASS['company']]
    context['fields_event'] = [(key, form.fields[key].label, form.fields[key].__class__.__name__)
                               for key in form.fields
                               if key in settings.VISITOR_FIELD_CLASS['event']]
    context['event'] = event_instance
    # edit = False
    # if (event_instance.companion_fields):
    #     edit = True
    # context['edit'] = edit

    return render(request, 'Event/event_companions.html', context)


@login_required
def event_payment(request, event_name):
    """Add/edit event description (wysiwyg editor)."""
    context = {}
    event_instance = utils.get_event_by_name(request, event_name)
    if ( event_instance.registration_step_finished < 6):
        event_instance.registration_step_finished = 6
        event_instance.save()
    event_profile = EventProfile.objects.filter(event=event_instance)

    days = (event_instance.end_time - event_instance.start_time).days
    days_choices = [(str(i+1), str(i+1) + ' days') for i in range(days+1)]
    days_choices.append(('Dinner', 'Dinner'))
    days_choices.append(('Track', 'Track'))
    days_choices = tuple(days_choices)
    PaymentTicketFormSet = getPaymentFormSet(days_choices)
    paypalObj = PaymentPayPal.objects.filter(event=event_instance)
    paypalObj = paypalObj[0] if paypalObj else None
    upnObj = PaymentUPN.objects.filter(event=event_instance)
    upnObj = upnObj[0] if upnObj else None
    if request.method == 'POST':
        paypal = PaymentPayPalForm(request.POST, instance=paypalObj).save(commit=False)
        if paypal:
            paypal.event = event_instance
            paypal.save()
        upn = PaymentUPNForm(request.POST, instance=upnObj).save(commit=False)
        if upn:
            upn.event = event_instance
            upn.save()

        if 'form-TOTAL_FORMS' in request.POST.keys():
            tickets_objs = PaymentTicket.objects.filter(event=event_instance)
            tickets = PaymentTicketFormSet(request.POST, queryset=tickets_objs)
            if tickets.is_valid():
                instances = tickets.save(commit=False)
                # add or refresh tickets
                for ticket in instances:
                    if ticket.ticket_name:
                        ticket.event = event_instance
                        ticket.save()
                # remove tickets
                for i in tickets.deleted_forms:
                    if i.instance.id:
                        i.instance.delete()
        form = EventPayment(request.POST, instance=event_instance)
        if form.is_valid():
            form.save()

            #by the below line we say that user finished adding the event
            if event_instance.registration_step_finished == 7:
                return redirect('add_event_payment', event_name=event_instance.subdomain)
            else:
                event_instance.registration_step_finished = 6
                event_instance.save()
                #return redirect('list_events')    
                return redirect('card_designer', event_name=event_instance.subdomain)
    else:
        #Fill tickets from payable tracks
        tickets_objs = PaymentTicket.objects.filter(event=event_instance)
        payable_tracks = Track.objects.filter(event=event_instance,
                                              track_is_payable=True)
        for track in payable_tracks:
            if not tickets_objs.filter(ticket_name=track.name):
                PaymentTicket(ticket_name=track.name,
                              event=event_instance,
                              days='Track',
                              track=track).save()

    context['form'] = EventPayment(instance=event_instance)
    context['form_pp'] = PaymentPayPalForm(instance=paypalObj)
    context['form_upn'] = PaymentUPNForm(instance=upnObj)
    context['form_ticket_empty'] = PaymentTicketFormSet(queryset=event_instance.tickets.filter(id__lt=0))
    context['formset'] = PaymentTicketFormSet(queryset=event_instance.tickets.all())
    context['event'] = event_instance
    if paypalObj:
        if paypalObj.paypal_enabled:
            context['paypal'] = 1
        else:
            context['paypal'] = 0
    else:
        context['paypal'] = 0
    if upnObj:
        if upnObj.upn_enabled:
            context['upn'] = 1
        else:
            context['upn'] = 0
    else:
        context['upn'] = 0

    return render(request, 'Event/event_payment.html', context)


#7th step
@login_required
def card_designer(request, event_name):
    """Step four companion information"""
    event_instance = utils.get_event_by_name(request, event_name)
    if (event_instance.registration_step_finished < 7):    
        event_instance.registration_step_finished = 7
        event_instance.save()
    context = {}
    context['event'] = event_instance
    #context['form'] = EventCardDesigner()

    if request.method == 'POST':
        return redirect('list_events')

    return render(request, 'Event/card_designer.html', context)


# -- TODO: Ce prav razumem tole kodo lahko vsak ki je logiran zbrise katerikoli event. !!
@login_required
def delete_event(request, event_name):
    if (Event.objects.filter(name=event_name).count() > 0):
        event_instance = utils.get_event_by_name(request, name=event_name)
        Event.objects.filter(name=event_name).delete()
        Lecture.objects.filter(event=event_instance).delete()
        PaymentUPN.objects.filter(event=event_instance).delete()
        PaymentPayPal.objects.filter(event=event_instance).delete()
        PaymentTicket.objects.filter(event=event_instance).delete()
        Track.objects.filter(event=event_instance).delete()
    return HttpResponse(status=200)


@login_required
@permission_required('Event.add_event')
def change_visitor_payed_status(request, event_name, active_filter):
    """Change payed status for visitor and redirect back to event data."""
    event_instance = utils.get_event_by_name(request, name=event_name)

    if request.method == 'POST':
        # -- Select the correct event profile entry.
        event_profile_instance = get_object_or_404(EventProfile, pk=request.POST['user_id'])

        if event_profile_instance.event == event_instance:
            if 'paymentStatus' in request.POST:
                event_profile_instance.payed = True
            else:
                event_profile_instance.payed = False
            event_profile_instance.save()

    if active_filter == 'payed':
        return redirect('event_users_data_payed',event_name=event_instance.subdomain)
    elif active_filter == 'not-payed':
        return redirect('event_users_data_not_payed', event_name=event_instance.subdomain)
    else:
        return redirect('event_users_data', event_name=event_instance.subdomain)


@login_required
def event_progress_users_data(request, event_name, realtime=None, addnew=None, lecture_id=None, download=None):
    """List users registered with the particular event. User list
    download and upload with IDs."""
    event_instance = utils.get_event_by_name(request, event_name)
    context = dict()
    context['event'] = event_instance
    form_update = ParticipantUpdate()

    # -- Determine which of the required fields are in EventProfile.
    file_fields = event_instance.participant_fields.copy()
    file_fields.extend(['payed', 'date_of_registration', 'note', 'uhf_id', 'barcode_no'])
    file_fields_extended_labels = {'payed': _('Payed'), 'date_of_registration': _('Date of Registration'), 'note': _('Note'), 'uhf_id': _('UHF ID'), 'barcode_no':_('barcode_no')}
    event_instance.participant_fields.extend(['payed', 'id', 'user', 'date_of_registration', 'note', 'uhf_id', 'barcode_no'])

    selected_fields = tuple(event_instance.participant_reqired_fields)
    lecture_status = None

    if addnew:
        form = ParticipantSoft()

        if request.method == 'POST':
            form = ParticipantSoft(request.POST)
            if form.is_valid():
                new_profile = form.save(commit=False)
                new_profile.event = event_instance
                new_profile.soft = True
                new_profile.is_finished = True
                new_profile.barcode_no = utils.generate_barcode(event_instance)
                new_profile.save()
                
                lectures = request.POST.getlist('lectureSignUp')

                new_profile.lectures.add(*lectures)
                new_profile.save()


                return redirect('event_progress_users_data', event_name=event_instance.subdomain)

        context['active_filter'] = 'addnew'
        participants = None
        context['form'] = form
    else:

        if request.method == 'POST':
            if 'event_profile_id' in request.POST:
                event_profile_instance = get_object_or_404(EventProfile, pk=request.POST['event_profile_id'])
                form_update = ParticipantUpdate(request.POST, instance=event_profile_instance)
                if form_update.is_valid():
                    form_update.save()
            elif 'participant' in request.POST:
                EventProfile.objects.filter(id__in=request.POST.getlist('participant')).delete()

        if realtime:
            context['active_filter'] = 'realtime'

            #lectures = Lecture.objects.filter(event=event_instance, start_time__lte=datetime.now().replace(tzinfo=pytz.utc),
            #                                end_time__gte=datetime.now().replace(tzinfo=pytz.utc))

            # -- List in progress and finished lectures.
            lectures = Lecture.objects.filter(event=event_instance, start_time__lte=datetime.now().replace(tzinfo=pytz.utc))#,
                                            #end_time__gte=datetime.now().replace(tzinfo=pytz.utc))                                            
            context['lectures'] = lectures

            if lecture_id:
                lecture_instance = lectures.get(id=lecture_id)
            else:
                lecture_instance = lectures.first()
            
            context['active_lecture'] = lecture_instance

            if not lecture_instance:
                participants = []
            elif lecture_instance.end_time < timezone.now():
                # -- If lecture ended already ...
                # ... do a simple algorithm for the time being. If entrance was detected,
                # ... that counts as visit.
                lecture_status = 'finished'

                api_data = UhfTime.objects.filter(event=event_instance,
                                                time_of_sec__gte=lecture_instance.start_time,
                                                time_of_sec__lte=lecture_instance.end_time).order_by('-id').filter(direction=0).distinct().values_list('user')
               
                participants = EventProfile.objects.values(*event_instance.participant_fields).filter(event=event_instance, user__in=api_data, is_companion=False)

            elif lecture_instance.end_time > timezone.now() and lecture_instance.start_time < timezone.now():
                # -- Lecture is currently in progress. Only show those, that are
                # ... actually present. It's bad if the machine doesn't register an event.
                lecture_status = 'inprogress'

                api_data = UhfTime.objects.filter(event=event_instance,
                                                time_of_sec__gte=lecture_instance.start_time,
                                                time_of_sec__lte=lecture_instance.end_time).order_by('-id').distinct().filter(direction=0).values_list('user')
                
                participants = EventProfile.objects.values(*event_instance.participant_fields).filter(event=event_instance, user__in=api_data, is_companion=False)
            
            else:
                # -- Lecture has not started yet.
                participants = []
            

            if download:
                return utils.csv_participants_in_progress_file(participants, file_fields, file_fields_extended_labels)
        
        else:
            context['active_filter'] = 'registered'
            participants = EventProfile.objects.values(*event_instance.participant_fields).order_by('-id').filter(event=event_instance, is_companion=False)

            if download:
                return utils.csv_participants_in_progress_file(participants, file_fields, file_fields_extended_labels)

        

    form = ParticipantFields(instance=event_instance)
    selected_fields_labels = [form.fields[key].label for key in selected_fields]

    context['participants'] = participants
    context['selected_fields'] = selected_fields
    context['selected_fields_labels'] = selected_fields_labels
    context['form_update'] = form_update
    context['lecture_status'] = lecture_status

    return render(request, 'Event/event_progress_users_data.html', context)

@login_required
def subdomain_check(request):
    print('here')
    subdomain = request.POST.get("subdomain", "")
    print(subdomain)
    count = Event.objects.filter(subdomain=subdomain).count()
    if (count > 0):
        return JsonResponse({'result':'taken'})
    else:
        return JsonResponse({'result':'free'})

@login_required
def save_card_outlook(request):
    print('here')
    data = request.POST.get("data", "")
    json_data = json.loads(data)

    subdomain = json_data['subdomain']
    count = Event.objects.filter(subdomain=subdomain).count()
    if (count == 1):
        event = Event.objects.filter(subdomain=subdomain).get()
        event.card_designer = json_data
        event.save()
    print(event)
    
    return JsonResponse({'result':'success'})
   