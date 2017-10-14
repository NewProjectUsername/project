from django.shortcuts import get_object_or_404

from Event.models import Event
from Visitor.models import EventProfile


def get_event_by_name_no_rights(name):
    event = get_object_or_404(Event, subdomain=name)

    return event

def get_event_profile_by_name(name):
	event_profile = EventProfile.objects.get(name=name)

	return event_profile