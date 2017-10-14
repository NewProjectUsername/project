import io
import csv
import datetime
import pytz
import itertools
import random

from model_utils.fields import AutoCreatedField, AutoLastModifiedField

from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.utils import timezone
from django.utils.translation import ugettext as _
import django.core.exceptions as django_exceptions
from django.utils.dateparse import parse_datetime
from django.db import transaction
from django.db.models import F
from django.contrib.auth import get_user_model

from Event.forms import EventLectures, GenericFileUploadForm, EventUsersIDs, ParticipantFields
from Event.models import Event, Track
from Visitor.models import EventProfile

User = get_user_model()

def handle_lectures_csv_file_upload(event_instance, file):
    """Handles the lecture file upload.

    Returns form object.
    """
    column_header = ['Name', 'Track', 'Payed Track', 'Start', 'End', 'Device ID', 'Lecture room', 'Bar tracking', 'Device entrance pos.']
    wrong_input_msg = _('Wrong input format.')

    csv_file = io.StringIO(file.read().decode())
    # -- Ignore the header line.
    csv_file = itertools.islice(csv_file, 1, None)
    content = list(csv.DictReader(csv_file, column_header))

    # -- First pass: add all tracks, if they are new.
    tracks = []
    for i, row in enumerate(content):
        tracks.append(row['Track'])

    tracks = list(set(tracks))

    for track in tracks:
        track = str(track)
        if track != '':
            existing = Track.objects.filter(event=event_instance, name=track).count()
            if existing == 0:
                new_track = Track(event=event_instance, name=track)
                new_track.save()

    # -- Second pass: add track_is_payable info, IF THERE IS AT LEAST ONE TRUE FOR THIS TRACK.
    list_of_payed_tracks = []
    list_of_free_tracks = []
    for i, row in enumerate(content):
        if row['Track'] != '':
            if ('TRUE' in row['Payed Track'].upper()):
                list_of_payed_tracks.append(row['Track'])
            else:
                list_of_free_tracks.append(row['Track'])

    # .. (first update free tracks, so that at least one payed True is enough)
    Track.objects.filter(event=event_instance, name__in=list_of_free_tracks).update(track_is_payable=False)
    Track.objects.filter(event=event_instance, name__in=list_of_payed_tracks).update(track_is_payable=True)


    for i, row in enumerate(content):
        try:
            # -- This below is so that the field without True is always false (regardles of the text inside).
            if 'TRUE' in row['Bar tracking'].upper():
                bar_tracking = True
            else:
                bar_tracking = False
            
            lecture_data = {'name': row['Name'],
                            'start_time': row['Start'],
                            'end_time': row['End'], 'lecture_room': row['Lecture room'],
                            'device_id': row['Device ID'], 'bar_tracking': bar_tracking,
                            'device_entrance_position': row['Device entrance pos.']}
            track = str(row['Track'])
            if track != '':
                lecture_data['track'] = Track.objects.get(event=event_instance, name=track).pk
            
            print(lecture_data)
            
        except (ValueError, KeyError) as e:
            form = GenericFileUploadForm()
            form.errors['file'] = ('line {}'.format(i), e, wrong_input_msg, )

            return form

        form = EventLectures(event_instance, lecture_data)

        if form.is_valid():
            new_lecture = form.save(commit=False)
            new_lecture.event = event_instance
            new_lecture.save()
        else:
            collected_errors = [(key, error[0]) for key, error in form.errors.items()]
            collected_errors.insert(0, 'in line {}'.format(i))
            _form = GenericFileUploadForm(lecture_data)
            #_form.errors['file'] = (wrong_input_msg, )
            _form.errors['file'] = collected_errors

            return _form

    return GenericFileUploadForm()



def csv_lecture_file(event_instance, lectures):
    """Takes a list of lectures and returns csv file response."""
    timezone = pytz.timezone(event_instance.timezone)
    column_header = [_('Name'), _('Track'), _('Payed Track'), _('Start'), _('End'), _('Device ID'), _('Lecture room'), _('Bar tracking'), _('Device entrance pos.')]

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="lectures.csv"'

    writer = csv.writer(response)
    # ['name', 'start_time', 'end_time', 'device_id', 'bar_tracking']
    writer.writerow(column_header)

    if lectures:
        # -- If lectures exist, create .csv from existing.
        for row in lectures:
            payable_track = ''
            if row.track:
                track = row.track.name
                if row.track.track_is_payable:
                    payable_track = 'True'
            else:
                track = ''
            writer.writerow([row.name, track, payable_track, str(row.start_time.astimezone(timezone).replace(tzinfo=None)),
                             str(row.end_time.astimezone(timezone).replace(tzinfo=None)), row.device_id, row.lecture_room,
                             row.bar_tracking, row.device_entrance_position])
    else:
        # -- If no lectures exist, send a sample .csv.
        #   .. First create some dates ...
        start_1 = (event_instance.start_time + datetime.timedelta(hours=1)).astimezone(timezone).replace(tzinfo=None)
        end_1 = (event_instance.end_time - datetime.timedelta(hours=3)).astimezone(timezone).replace(tzinfo=None)
        start_2 = (event_instance.start_time + datetime.timedelta(hours=3)).astimezone(timezone).replace(tzinfo=None)
        end_2 = (event_instance.end_time - datetime.timedelta(hours=2)).astimezone(timezone).replace(tzinfo=None)

        #   .. Then write to csv and return.
        writer.writerow([_('Coctail party'),  _('Bussiness track'), '', str(start_1),
                         str(end_1), '123456', _('Room I'), 'True', 'R'])
        writer.writerow([_('Plenary lecture'), '', '', str(start_2),
                         str(end_2), '55555', '', '', 'L'])
        writer.writerow([_('Plenary lecture in track'), _('Expensive track'), 'True', str(start_2),
                         str(end_2), '55555', _('Room I'), '', 'L'])

    return response

def csv_participants_file(participants, fields):
    """Takes a list of participants and returns csv file response."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="{}.csv"'.format(_('user_ids'))

    title_row = [_('User ID'), _('UHF ID'), _('Barcode Nr.')]
    participants_form = ParticipantFields()
    all_fields = participants_form.fields
    for key in fields:
        title_row.append(all_fields[key].label)

    writer = csv.writer(response)
    # ['name', 'start_time', 'end_time', 'device_id', 'bar_tracking']
    writer.writerow(title_row)

    for row in participants:
        # -- Dealing with empty fields.
        if not row.uhf_id:
            user_row = [row.pk, '']
        else:
            user_row = [row.pk, row.uhf_id]
        if row.barcode_no:
            user_row.append(row.barcode_no)
        else:
            user_row.append('')
        
        for key in fields:
            if 'birth_year' in key:
                birth_year = getattr(row, key)
                if birth_year:
                    user_row.append(birth_year.strftime('%d. %m. %Y'))
                else:
                    user_row.append('')
            else:
                user_row.append(getattr(row, key))

        writer.writerow(user_row)


    return response

def handle_id_csv_file_upload(event_instance, file):
    """Handles the user ids file upload.

    Returns form object.
    """
    # -- Create a new event instance, the one you got has been modified,
    #   has extra fields.
    event_instance = Event.objects.get(pk=event_instance.id)

    # -- Get all fields, and all fields for event.
    participant_form = ParticipantFields()
    all_fields = participant_form.fields
    field_keys = event_instance.participant_fields

    # -- Title labels that tie fields to column headers.
    title_labels = [all_fields[key].label for key in field_keys]

    csv_file = io.StringIO(file.read().decode())
    csv_file = itertools.islice(csv_file, 1, None)
    title_row = ['User ID', 'UHF ID', 'Barcode Nr.']
    title_row.extend(title_labels)
    content = csv.DictReader(csv_file, title_row)

    try:
        with transaction.atomic():
            for i, row in enumerate(content):
                # -- Special cases that must be handled (either integer or empty)
                if row['User ID'] == '':
                    user_id = None
                else:
                    user_id = row['User ID']
                if row['UHF ID'] == '':
                    uhf_id = None
                else:
                    uhf_id = row['UHF ID']
                if row['Barcode Nr.'] == '':
                    barcode = None
                else:
                    barcode = row['Barcode Nr.']
                
                defaults_dict = dict(uhf_id=uhf_id, barcode_no=barcode)

                for key in field_keys:
                    # -- Birth year needs special formatting.
                    if 'birth_year' in key:
                        if row[all_fields[key].label] != '':
                            defaults_dict[key] = datetime.datetime.strptime(
                                row[all_fields[key].label], '%d. %m. %Y'
                            )
                    # -- Boolean needs casting.
                    elif 'BooleanField' in all_fields[key].__class__.__name__:
                        defaults_dict[key] = bool(row[all_fields[key].label])
                    # -- Integer can be empty.
                    elif 'IntegerField' in all_fields[key].__class__.__name__:
                        value = row[all_fields[key].label]
                        if value == '':
                            defaults_dict[key] = None
                        else:
                            defaults_dict[key] = value
                    # -- All other, 'normal' cases.
                    else:
                        defaults_dict[key] = row[all_fields[key].label]
                
                # -- Create participant entry.
                defaults_dict['is_finished'] = True
                obj, created = EventProfile.objects.update_or_create(
                    pk=user_id, event_id=event_instance.id,
                    defaults=defaults_dict
                    )
                # -- Clear existing lectures, if entry exists.
                if not created:
                    obj.lectures.clear()
                # -- Add all lectures from event.
                obj.lectures.add(*event_instance.lecture_set.all())
    except (ValueError, KeyError, django_exceptions.ObjectDoesNotExist) as e:
        form = GenericFileUploadForm()
        form.errors['file'] = (_('Wrong input format.'), e)
        # -- TODO: Sentry report?

        return form

    return GenericFileUploadForm()


def upn_references_csv_export(event_instance):
    """Print name | surname | upn_reference for each
    user for this event. Only send upns where they exist? yes."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="{}.csv"'.format(_('visitor_upn_references'))

    title_row = [_('Username'), _('Name'), _('Surname'), _('UPN Reference')]

    visitors = EventProfile.objects.filter(event=event_instance)

    writer = csv.writer(response)
    writer.writerow(title_row)
    for visitor in visitors:
        if visitor.upn_reference:
            writer.writerow([visitor.user.username, visitor.name, visitor.surname, visitor.upn_reference])

    return response

def csv_participants_in_progress_file(participants, fields, extended_labels):
    """Takes a list of participants and returns csv file response."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="{}.csv"'.format(_('participants'))

    title_row = []
    participants_form = ParticipantFields()
    all_fields = participants_form.fields
    for key in fields:
        if key in all_fields:
            title_row.append(all_fields[key].label)
        elif key in extended_labels:
            title_row.append(extended_labels[key])

    writer = csv.writer(response)
    # ['name', 'start_time', 'end_time', 'device_id', 'bar_tracking']
    writer.writerow(title_row)

    for row in participants:
        user_row = []
        for key in fields:
            user_row.append(row[key])

        writer.writerow(user_row)


    return response

def get_event_by_name(request, name):
    event = get_object_or_404(Event, subdomain=name)
    if event.user == request.user:
        return event
    else:
        raise Http404(_('Da te ne vidim več hekat eventov'))

def get_event_by_name_public(request, name):
    event = get_object_or_404(Event, subdomain=name)
    return event
    

def register_users_for_event(event, nr=500, length=8):
    """Generates users and registers them for the supplied event."""
    import random, string
    from Visitor.models import Profile, EventProfile

    participants_form = ParticipantFields()

    participant_fields = dict([(key, participants_form.fields[key].label) for key in participants_form.fields.keys()
                                if key in event.participant_fields])

    UserModel = get_user_model()

    for i in range(nr):
        username = ''.join(random.choice(string.ascii_lowercase) for i in range(length))
        payed = random.choice([True, False])
        has_upn_reference = random.choice([True, False])

        participant_fields = dict([(key, ''.join(random.choice(string.ascii_lowercase) for i in range(length)).title()) for key in participants_form.fields.keys()
                                    if key in event.participant_fields])

        if has_upn_reference:
            participant_fields['upn_reference'] = 1234

        user = UserModel.objects.create_user(username, password='idconference666')
        
        event_profile = EventProfile(user=user,
                                     event=event,
                                     payed=payed,
                                     barcode_no=generate_barcode(event),
                                     **participant_fields)
        event_profile.save()        


def get_uhf_data(csv_file, nr=None):

    column_header = ['pk', 'direction', 'time_of_sec', 'user']

    with open(csv_file, 'r') as f:
        csv_file = io.StringIO(f.read())
        # -- Ignore the header line.
        csv_file = itertools.islice(csv_file, 1, None)
        content = list(csv.DictReader(csv_file, column_header))

    return content

def create_users_and_map(data, event_object):
    # -- Get user ids from uhf data.
    orphants = [entry['user'] for entry in data]

    # -- Make a list of all users.
    orphant_set = set(orphants)

    # -- Check how many users are there.
    user_nr = len(orphant_set)

    # -- There should be at least this many users in model.
    user_model = get_user_model()
    nr = len(user_model.objects.all())
    if nr < user_nr:
        register_users_for_event(event_object, user_nr - nr)

    # -- If everything is ok, create a mapping in a form of a dict.
    user_map = dict()
    real_users = user_model.objects.all()[:user_nr]
    for orphant, real_user in zip(orphant_set, real_users):
        user_map[int(orphant)] = real_user

    return user_map

def enter_uhf_data(event_object, api_model, device_id, csv_file, timedelta=None):
    # -- Clean existing data.
    api_model.objects.all().delete()

    print('Reading uhf data from csv.')
    data = get_uhf_data(csv_file)

    print('Mapping uhf users to model users.')
    user_map = create_users_and_map(data, event_object)

    print('Reading uhf data from csv.')
    data = get_uhf_data(csv_file)

    print('Populating uhf table.')
    entries = []
    for entry in data:
        if timedelta:
            entry_time = (parse_datetime(entry['time_of_sec']) + timedelta).replace(tzinfo=None)
        else:
            entry_time = parse_datetime(entry['time_of_sec']).replace(tzinfo=None)
        entries.append(api_model(user=user_map[int(entry['user'])], device_id=device_id,
                                 direction=entry['direction'], event=event_object,
                                 time_of_sec=entry_time))
    api_model.objects.bulk_create(entries)

def shift_uhf_times_to_now(uhf_model):
    """Check smallest time and calculate delta to now, then shift all times with
    that delta.
    
    Short how-to
    ------------

        >>>ut.enter_uhf_data(Event.objects.first(), UhfTime, 1234, 'notebooks/uhf.csv')
        >>>timed = ut.shift_uhf_times_to_now(UhfTime)
        >>>ut.enter_uhf_data(Event.objects.first(), UhfTime, 1234, 'notebooks/uhf.csv', timed)
    
    """
    timezone.deactivate()
    # -- Check earliest datetime.
    first_entry_time = uhf_model.objects.all().order_by('time_of_sec').first().time_of_sec.replace(tzinfo=None)
    now = timezone.now().replace(tzinfo=None)

    # -- Calculated difference to now.
    time_difference = now - first_entry_time
    time_difference = time_difference

    # -- Add this difference to all entries.
    #uhf_model.objects.all().update(time_of_sec=F('time_of_sec') + time_difference)

    return time_difference


def generate_barcode(event):
    rand = 0
    rand = random.randint(1,1323421232)*3

    if len(EventProfile.objects.filter(event=event, barcode_no=rand)) != 0:
        rand = random.randint(1,1323421232)*3
    else:   
        return rand
