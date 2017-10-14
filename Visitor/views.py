from datetime import date
from datetime import timedelta
import operator
import collections
from collections import defaultdict
import json

from django.core import serializers
from django.http import HttpResponse
from django.shortcuts import render, redirect, Http404
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect, Http404, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.forms.models import model_to_dict
from django.utils.translation import ugettext_lazy as _
from django.db.models import Count
from django.db.models.functions import ExtractDay, TruncDate

from Ideconference.settings import VISITOR_FIELD_CLASS

from Event.models import Event, PaymentTicket, Lecture, Track
from django.template import loader
from .forms import VisitorForm
from Event.models import Event
from Event.forms import ParticipantFields, CompanionFields
import Event.utils as utils

from Landing.forms import RegisterUser

from .models import EventProfile
from .forms import VisitorForm
from Ideconference.settings import VISITOR_FIELD_CLASS
from django.utils.translation import ugettext_lazy as _
from wkhtmltopdf.utils import RenderedFile, render_pdf_from_template

from mail_templated import EmailMessage
from .utils import get_event_by_name_no_rights
from .utils import get_event_profile_by_name

from datetime import datetime

import paypalrestsdk
import logging
# Create your views here.


def add_visitor(request):
    
    event = Event.objects.filter(subdomain=request.subdomain)
    context = {}
    if request.method == "POST":
        ivan = VisitorForm(request.POST)
        if ivan.isValid():
            ivan.save(commit=False)
            ivan.user = request.user
            ivan.save()
        else:
            pass
    if event:
        event = event[0]
        context['event_name'] = event.name
        context['form'] = VisitorForm(event.participant_fields,
                                      event.participant_reqired_fields)
    else:
        context['alert'] = str(request.subdomain)
    return render(request, 'Visitor/visitor.html', context)


def visitor_registration_participant_information(request, event_name=False):
    event_instance = get_event_by_name_no_rights(event_name)

    if event_instance.participant_reqired_fields:
        required_fields = event_instance.participant_reqired_fields
    else:
        required_fields = ['name', 'surname']

    if request.user.is_authenticated():
        initial_fields = model_to_dict(request.user.profile, fields=event_instance.participant_fields)
        # -- First check if user was registered for any events already.
        last_event_profile = EventProfile.objects.filter(user=request.user).order_by('-id').first()
        if last_event_profile:
            # -- Set initial fields from last event registration.
            for field in last_event_profile.event.participant_fields:
                initial_fields[field] = getattr(last_event_profile, field)
        # -- Override first and last name with profile data.
        if 'name' in event_instance.participant_fields:
            initial_fields['name'] = request.user.first_name
        if 'surname' in event_instance.participant_fields:
            initial_fields['surname'] = request.user.last_name
    else:
        initial_fields = None
        required_fields = [field for field in required_fields if field not in ['name', 'surname']]

    new_user_form = RegisterUser(prefix='registration')

    event_profile = None
    if (request.user.is_authenticated()):
        #this needs to be checked
        event_profile = EventProfile.objects.filter(event=event_instance, user=request.user, is_companion=0).first()
    if event_profile:
        form = ParticipantFields(required_fields=required_fields, prefix='participant', instance=event_profile)
    else:    
        print('here')
        form = ParticipantFields(required_fields=required_fields, initial=initial_fields, prefix='participant')    

    if request.method == 'POST':
        # -- Ce user se ni logiran ga usput registriraj in logiraj.
        if not request.user.is_authenticated():
            new_user_form = RegisterUser(request.POST, prefix='registration')

            if new_user_form.is_valid():
                new_user_form.save()

                email = new_user_form.cleaned_data.get('email')
                password = new_user_form.cleaned_data.get('password1')

                user = authenticate(email=email, password=password)
                login(request, user)

                form = ParticipantFields(request.POST, required_fields=required_fields, prefix='participant',instance=event_profile)
                if form.is_valid():
                    new_profile = form.save(commit=False)
                    new_profile.user = user
                    new_profile.event = event_instance
                    new_profile.name = user.first_name
                    new_profile.surname = user.last_name
                    new_profile.registration_step_finished = 1
                    new_profile.barcode_no = utils.generate_barcode(event_instance)
                    new_profile.save()

                    return redirect('companion_info', event_name=event_instance.subdomain)
        #to do
        else:
            check_existing_registration = EventProfile.objects.filter(
                user=request.user,
                event=event_instance).count()
            #if check_existing_registration > 0:
                #event_profile = check_existing_registration.first()

            form = ParticipantFields(request.POST, required_fields=required_fields, prefix='participant', instance=event_profile)
            if form.is_valid():
                new_profile = form.save(commit=False)
                new_profile.user = request.user
                new_profile.event = event_instance
                new_profile.barcode_no = utils.generate_barcode(event_instance)
                if new_profile.registration_step_finished < 2:
                    new_profile.registration_step_finished = 1
                new_profile.save()

                return redirect('companion_info', event_name=event_instance.subdomain)

    
    if not request.user.is_authenticated():
        personal_fields = [key for key in event_instance.participant_fields
                            if key in VISITOR_FIELD_CLASS['personal'] and key not in ['name', 'surname']]
    else:
        personal_fields = [key for key in event_instance.participant_fields
                            if key in VISITOR_FIELD_CLASS['personal']]
    company_fields = [key for key in event_instance.participant_fields
                       if key in VISITOR_FIELD_CLASS['company']]
    event_fields = [key for key in event_instance.participant_fields
                     if key in VISITOR_FIELD_CLASS['event']]
                                    

    context = dict(event=event_instance, form=form, personal_fields=personal_fields,
                   company_fields=company_fields, event_fields=event_fields, new_user_form=new_user_form, event_profile=event_profile)    

    return render(request, 'Visitor/visitor_registration_participant_information.html', context)

@login_required
def visitor_registration_companion_information(request, event_name=False):
    event_instance = get_event_by_name_no_rights(event_name)

    # -- If there is no fields specified for companion,
    # .. redirect user to the next step.
    if not event_instance.companion_fields:
        return redirect('events_selector_visitor', event_name=event_instance.subdomain)
    
    if event_instance.companion_reqired_fields:
        required_fields = event_instance.companion_reqired_fields
    else:
        required_fields = []

    #this is the profile of the visitor that wants to register (person from the first step)    
    event_profile = EventProfile.objects.filter(event=event_instance, user=request.user, is_companion=0).first()
    if (event_profile.registration_step_finished < 2):
        event_profile.registration_step_finished = 2    
        event_profile.save()

    #retrieveing the list of existing companion_profilesa
    companion_profiles = EventProfile.objects.filter(event=event_instance, user=request.user, is_companion=1)
   
    form = CompanionFields(required_fields=required_fields)

    if request.method == 'POST':
        #when we select edit companion from the list of companions
        #we want therefore serve form that has instance already predefined
        if 'edit' in request.POST:
            name = request.POST.get('name');
            surname = request.POST.get('surname');
            companion_profile = EventProfile.objects.filter(event=event_instance, user=request.user, name=name, surname=surname, is_companion=1).first()
            form = CompanionFields(request.POST, required_fields=required_fields, instance=companion_profile)
        elif 'delete' in request.POST:
            name = request.POST.get('name');
            surname = request.POST.get('surname');
            companion_profile = EventProfile.objects.filter(event=event_instance, user=request.user, name=name, surname=surname, is_companion=1).first()
            companion_profile.delete() 
        else:
            form = CompanionFields(request.POST, required_fields=required_fields)     
            if form.is_valid():
                new_profile = form.save(commit=False)
                new_profile.user = request.user
                new_profile.event = event_instance
                new_profile.is_companion = True
                new_profile.save()

                # -- If user wants to add another companion ...
                if 'new' in request.POST:
                    return redirect('companion_info', event_name=event_instance.subdomain)
                else:
                    # -- Redirect to the next step (step3)
                    return redirect('events_selector_visitor', event_name=event_instance.subdomain)

    if event_instance.companion_fields:

        personal_fields = [key for key in event_instance.companion_fields
                            if key in VISITOR_FIELD_CLASS['personal']]
        company_fields = [key for key in event_instance.companion_fields
                           if key in VISITOR_FIELD_CLASS['company']]
        event_fields = [key for key in event_instance.companion_fields
                         if key in VISITOR_FIELD_CLASS['event']]
    else:
        # -- Redirect to next step if no companion.
        return redirect('events_selector_visitor', event_name=event_instance.subdomain)

    context = dict(event=event_instance, form=form, personal_fields=personal_fields,
                   company_fields=company_fields, event_fields=event_fields, companion_profiles=companion_profiles)

    return render(request, 'Visitor/visitor_registration_companion_information.html', context)

@login_required
def visitor_registration_events_selector(request, event_name):
    """Step three - user selects the events he will be participating"""
    event_instance = get_event_by_name_no_rights(event_name)
    event_profile_check = EventProfile.objects.filter(user=request.user, event=event_instance).count()
    #is this if event necessary? It will not be possible for the user to 
    if event_profile_check == 0:
        event_profile = EventProfile.objects.create(user=request.user, event=event_instance)  
        event_profile.registration_step_finished = 3
        event_profile.save()
    else:
        event_profile = EventProfile.objects.filter(user=request.user, event=event_instance).first() 
        if event_profile.registration_step_finished < 3:
            event_profile.registration_step_finished = 3
            event_profile.save()


    #getting all the tickets to this event    
    tickets = PaymentTicket.objects.filter(event=event_instance)
    #the field day is added to the result
    #lectures =Lecture.objects.filter(event=event_instance).annotate(day=TruncDate('start_time')).values('day', 'id', 'name', 'start_time', 'end_time', 'track__name').order_by('day')
    lecturesTemp = Lecture.objects.filter(event=event_instance)

    lectures = defaultdict(list)
    for lT in lecturesTemp:
        if (lT.start_time.date() != lT.end_time.date()):
            delta = lT.end_time.date() - lT.start_time.date()
            for i in range(delta.days+1):
                lectures[lT.start_time.date() + timedelta(days=i)].append(lT)
        else:
            lectures[lT.start_time.date()].append(lT)        

    #getting all the track for this event        
    tracks = Track.objects.filter(event=event_instance)

    #1. step - get individually payable tracks in the dictionay, where key is track id and value is price
    payableTracks = {}
    for track in tracks:
        if track.track_is_payable:
            #we need to retrieve the price of the ticket
            payment_ticket = PaymentTicket.objects.get(track=track)
            payableTracks[track.name] = payment_ticket.price      

    #2.step - determine which lectures belong to specific track
    tracksAndLectures = {}
    groupsTracks = defaultdict(list)
    for track in tracks:
        lecturesByTrack = Lecture.objects.filter(track=track)
        lecturesTemp = list()
        lecturesFullTemp = list()
        for lec in lecturesByTrack:
            lecturesTemp.append(lec.name) 
            lecturesFullTemp.append(lec)
        tracksAndLectures[track.name] = lecturesTemp
        groupsTracks[track.name] = lecturesFullTemp
    js_data = json.dumps(tracksAndLectures)  

    groupsTracks = collections.OrderedDict(sorted(groupsTracks.items()))  
    
    groupsTracksJson = {}
    for v in groupsTracks:
        arrayTemp = []
        lectTemp = groupsTracks[v]
        for lt in lectTemp:
            id = lt.id
            track = v
            if track in groupsTracksJson:
                arrayTemp = groupsTracksJson[track]
                arrayTemp.append(id)
                groupsTracksJson[track] = arrayTemp
            else:
                arrayTemp.append(id)
                groupsTracksJson[track] = arrayTemp
                
    #3. step - for daily tickets
    ticketsArranged = {}
    for ticket in tickets:
        ticketsArranged[ticket.days] = ticket.price

    js_data_tickets = json.dumps(ticketsArranged)
 

    #this is needed for the visualization
    groups = defaultdict(list)
    groupsJson = {}
    #we group a dictionary of lists
    for obj in lectures:
        arrayTemp = []
        #groups[obj['day']].append(obj)
        lectTemp = lectures[obj]
        for lt in lectTemp:
            id = lt.id
            date = str(obj)
            if date in groupsJson:
                arrayTemp = groupsJson[date]
                arrayTemp.append(id)
                groupsJson[date] = arrayTemp
            else:
                arrayTemp.append(id)
                groupsJson[date] = arrayTemp
    #and then we sort the dictionary to ordered dictionary  
    d = collections.OrderedDict(sorted(lectures.items()))

    #4. step - counting the number of lectures per day - 
    #needed for the "whole day checkbox"
    lecturesPerDay = {}
    for index,value in groups.items():
        lecturesPerDay[str(index)] = len(value);

    js_lectures_per_day = json.dumps(lecturesPerDay)  

    #this is needed for determining if checked lectures are on the different day and for
    #dictionay is holding id of lecture as key and day of the lecture as value - needed to easily check on which day is lecture and
    #for easier calculation of ticket price
    lectIds = {}
    for obj in lectures:
        dayValue = str(obj);
        for l in lectures[obj]:
            if (l.id in lectIds):
                daysTemp = list()
                daysTemp = lectIds[l.id]
                daysTemp.append(dayValue)
                lectIds[l.id] = daysTemp
            else:
                daysTemp = [dayValue]
                lectIds[l.id] = daysTemp    

    lectIdsJson = json.dumps(lectIds)

    #number of days of the event are needed to know number of coloumns for the visualisation in the template
    #delta = (end_day - start_day).days+1
    col_width = 2
    if len(lectures) != 0:
        delta = len(lectures)
    else:
        delta = 1    

    if delta > 5 and delta <= 12:
        col_width = 1
    if delta < 5:
        col_width = 12/delta 
    if delta == 5:
        col_width = 2 


    #with these we retrieve if any lectures were already selected
    selected_lectures = []
    previous_lectures = event_profile.lectures.all();
    for lec in previous_lectures:
        selected_lectures.append(lec.id)    

    if request.method == 'POST':
        lectures_list = request.POST.getlist('lectures[]')
        print(lectures_list)
        #since lecture can span for longer than one day, it can be added twice into checkbox list
        #therefore we need set
        lec_list = set(lectures_list)
        allTracks = {}
        #getting all the tracks and their prices
        for lec_id in lec_list:
            count = Lecture.objects.filter(id=lec_id).count()
            if count > 1 and (lecture.track.name in payableTracks):
                allTracks[lecture.track.name] = payableTracks[lecture.track.name];
        

        #getting all days and their prices
        #for lI in lectIds
        days = set()
        for key, value in lectIds.items():
            if str(key) in lec_list:
                days.update(value)
        
        #getting ticket name and price
        numDays = len(days)
        dayAndPrice = {}
        #it can happen that there is no ticket for proposed number of days
        #we then try to take first ticket for less days and presume that other days are free
        count = PaymentTicket.objects.filter(event=event_instance, days=numDays).count()
        if count > 0:
            ticket = PaymentTicket.objects.filter(event=event_instance, days=numDays).get()
            #TO-DO needed also for dinner and other stuff
            dayAndPrice[ticket.ticket_name] = ticket.price
        else:
            while (numDays > 1 or len(dayAndPrice) == 0):
                numDays -= 1;
                countNew = PaymentTicket.objects.filter(event=event_instance, days=numDays).count()
                if (countNew > 1):
                    ticket = PaymentTicket.objects.filter(event=event_instance, days=numDays).get()
                    dayAndPrice[ticket.ticket_name] = ticket.price

        print('ticket')            
        print(dayAndPrice)    


        #TO-DO also to consider tickets for dinner and other stuff
        sumDays = dayAndPrice[ticket.ticket_name]
        sumTracks = 0
        for key, value in allTracks.items():
            sumTracks = sumTracks + value
  

        if sumTracks > sumDays:    
            event_profile.for_pay = sumDays
            payDetails = json.dumps(dayAndPrice)
            event_profile.pay_details = payDetails
        elif sumDays > sumTracks: 
            event_profile.for_pay = sumTracks
            payDetails = json.dumps(allTracks)
            event_profile.pay_details = payDetails   


        price_days = request.POST['payPerDay']
        price_tracks = request.POST['payPerTrack']
        #todo calculated ticket value
        print(lectures_list)
        if (len(lectures_list) > 0):
            for lecture_id in lectures_list:
                lecture = Lecture.objects.get(pk=lecture_id)
                event_profile.lectures.add(lecture)
            event_profile.save()  

        return redirect('payment', event_name=event_instance.subdomain)

    #else if not post
    start_day = event_instance.start_time.date()
    end_day = event_instance.end_time.date()

    num_of_days = len(lectures)   
    context = {}
    context['tickets'] = js_data_tickets
    context['tracksAndLectures'] = js_data
    context['lectures'] = lectures
    context['payable_tracks'] = payableTracks
    context['lecturesDays'] = lectIdsJson
    context['groupsDays'] = d
    context['groupsTracks'] = groupsTracks
    context['groupsJson'] = json.dumps(groupsJson)
    context['groupsTracksJson'] = json.dumps(groupsTracksJson)
    context['event'] = event_instance
    context['num'] = delta
    context['selected_lectures'] = selected_lectures
    context['col_width'] = int(col_width)
    context['lecturesPerDay'] = js_lectures_per_day

    return render(request, 'Visitor/visitor_registration_events_selector.html', context)



@login_required
def visitor_registration_payment(request, event_name=False):
    print("payment")
    event_instance = get_event_by_name_no_rights(event_name)

    event_profile = None
    if (request.user.is_authenticated()):
        #this needs to be checked
        event_profile = EventProfile.objects.filter(event=event_instance, user=request.user, is_companion=0).first()

        if event_profile.registration_step_finished < 4:
            event_profile.registration_step_finished = 4
            event_profile.save()
    context = {"event": event_instance}
    profile = get_object_or_404(EventProfile,
                                event=event_instance,
                                user=request.user)

    context['articles'] = profile.pay_details
    context['total'] = ('Total', profile.for_pay)
    context['payments'] = [i.get_payments() for i in event_instance.payment.all()]
    context['event_profile'] = event_profile
    print(context['payments'])

    return render(request, 'Visitor/visitor_payment.html', context)


@login_required
def send_upn(request, event_name=False):
    event_instance = get_event_by_name_no_rights(event_name)
    profile = get_object_or_404(EventProfile,
                                event=event_instance,
                                user=request.user)
    context = {'event': event_instance,
               'profile': profile,
               'date': datetime.now(),
               'date_to': date.today() + timedelta(days=10)}

    for payment in event_instance.payment.all():
        t_payment = payment.get_payments()
        if t_payment[0] == 'UPN':
            context['payment'] = t_payment[1]
            break

    print(context)
    return_file = "tmp/" + 'upn_' + event_instance.name + '_' + str(profile.id) + '.pdf'

    t = loader.get_template('Visitor/email/upn.html')
    #DEBUG FOR UPN
    #return render(request, 'Visitor/email/upn.html', context)
    response = render_pdf_from_template(request=request,
                                        context=context,
                                        input_template=t,
                                        header_template='',
                                        footer_template='',
                                        )

    message = EmailMessage('Visitor/email/base_email.html',
                           {'user': profile}, 'info@kongres.identiks.webfactional.com',#event_instance.sent_mail,
                           to=[profile.user.email])
    message.attach('invoice.pdf', response, 'application/pdf')
    message.send()

    return render(request, 'Visitor/mail_redirect.html', {})


def create_paypal(request, event_name=False):
    paypalrestsdk.configure({
      "mode": "sandbox", # sandbox or live
      "client_id": "AXnjnX8k0VYQHwLd08syg5dNaM3-Yl_7jPleOmfZtt7r2az5rfyT_bOyLCubbEThKca-N1AcF1CN8IxI",
      "client_secret": "EIVvBxgzdowasfSR4QrMVyDMXH3qCdiDnqyv6AHkYwpg3mQ5DfsBeJc0ijSqw6XUoHK70765aBLv-Rrx" })
    event_instance = get_event_by_name_no_rights(event_name)
    profile = get_object_or_404(EventProfile,
                                event=event_instance,
                                user=request.user)


    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {
            "payment_method": "paypal"},
        "redirect_urls": {
            "return_url": "http://localhost:8000/visitor/payment/" + event_name + "/execute",
            "cancel_url": "http://localhost:8000/visitor/payment/"},
        "transactions": [{
            "item_list": {
                "items": [{
                    "name": "Konferenca",
                    "sku": "Pac neki karkoli",
                    "price": str(profile.for_pay),
                    "currency": "EUR",
                    "quantity": 1}]},
            "amount": {
                "total": str(profile.for_pay),
                "currency": "EUR"},
            "description": "to je konferenca"}]})

    if payment.create():
      print("Payment created successfully")
      for link in payment.links:
        print(link)
        if link.rel == "approval_url":
            print (link.href)
            # Convert to str to avoid google appengine unicode issue
            # https://github.com/paypal/rest-api-sdk-python/pull/58
            approval_url = str(link.href)
            return redirect(approval_url)
    else:
        print(vars(payment))
    return redirect('payment', event_name=event_name)


def proceed_paypal(request):
    context = {"status": "neki neki"}
    return render(request, 'Visitor/paypal_response.html', context)
