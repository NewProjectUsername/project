# -*- coding: utf-8 -*-
from django.conf.urls import include, url

from .views import *

urlpatterns = [
	#url(r'login', event_login, name='event_login'),
	url(r'visitor', add_visitor, name='add_visitor'),
	url(r'^register/(?P<event_name>.+)/participant-info', visitor_registration_participant_information, name='participant_info'),
	url(r'^register/(?P<event_name>.+)/participant-info', visitor_registration_participant_information, name='participant_info'),
	url(r'^register/(?P<event_name>.+)/companion-info', visitor_registration_companion_information, name='companion_info'),
	url(r'^register/(?P<event_name>.+)/events-selector', visitor_registration_events_selector, name='events_selector_visitor'),
	url(r'^register/(?P<event_name>.+)/payment', visitor_registration_payment, name='payment'),
	url(r'^register/(?P<event_name>.+)/send_upn', send_upn, name='send_upn'),
	url(r'^payment/(?P<event_name>.+)/', create_paypal, name='create_paypal'),
	url(r'^payment/(?P<event_name>.+)/execute/', create_paypal, name='paypal_execute'),
	]