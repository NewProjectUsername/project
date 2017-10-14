# -*- coding: utf-8 -*-
from django.conf.urls import include, url
from .views import *

urlpatterns = [
    url(r'^add/$', add_event, name='add_event'),
    url(r'^modify/(?P<event_name>.+)/$', add_event, name='modify_event'),
    url(r'^list/$', list_events, name='list_events'),
    url(r'^participants/(?P<event_name>.+)/$', event_participants, name='add_event_participants'),
    url(r'^payment/(?P<event_name>.+)/$', event_payment, name='add_event_payment'),
    url(r'^progress-data/(?P<event_name>.+)/real-time/(?P<lecture_id>[0-9]+)/$', event_progress_users_data, {'realtime': True},name='event_progress_users_data_real_time_lecture'),
    url(r'^progress-data/(?P<event_name>.+)/real-time/download$', event_progress_users_data, {'realtime': True, 'download': True},name='event_progress_users_data_real_time_download'),
    url(r'^progress-data/(?P<event_name>.+)/real-time/$', event_progress_users_data, {'realtime': True}, name='event_progress_users_data_real_time'),
    url(r'^progress-data/(?P<event_name>.+)/add-new/$', event_progress_users_data, {'addnew': True}, name='event_progress_users_data_add_new'),
    url(r'^progress-data/(?P<event_name>.+)/download/$', event_progress_users_data, {'download': True}, name='event_progress_users_data_download'),
    url(r'^progress-data/(?P<event_name>.+)/$', event_progress_users_data, name='event_progress_users_data'),
    url(r'^data/(?P<event_name>.+)/$', event_users_data, {'payed': 'all'}, name='event_users_data'),
    url(r'^data/(?P<event_name>.+)/payed$', event_users_data, {'payed': 'payed'}, name='event_users_data_payed'),
    url(r'^data/(?P<event_name>.+)/not-payed$', event_users_data, {'payed': 'not-payed'}, name='event_users_data_not_payed'),
    url(r'companions/(?P<event_name>.+)', event_companion, name='add_event_companion'),
    url(r'^description/(?P<event_name>.+)/$', add_event_description, name='add_event_description'),
    url(r'^lectures/download/(?P<event_name>.+)/(?P<download>[0-9]+)/$', add_event_lectures, name='download_csv_sample'),
    url(r'^lectures/add-track/(?P<event_name>.+)/(?P<add_track>[0-9]+)/$', add_event_lectures, name='add_event_track'),
    url(r'^lectures/remove/(?P<event_name>.+)/(?P<lecture_id>[0-9]+)/$', remove_event_lecture, name='remove_event_lecture'),
    url(r'^lectures/modify/(?P<event_name>.+)/(?P<lecture_id>[0-9]+)/$', modify_event_lecture, name='modify_event_lecture'),
    url(r'^lectures/(?P<event_name>.+)/$', add_event_lectures, name='add_event_lectures'),
    url(r'^card_designer/(?P<event_name>.+)/$', card_designer, name='card_designer'),
    url(r'^user-list/download/upn/(?P<event_name>.+)/$', download_event_users_upn_references, name='download_event_users_upn'),
    url(r'^user-list/download/(?P<event_name>.+)/(?P<payed>.+)/$', download_event_users_data, name='download_event_users_data'),
    url(r'^delete_event/(?P<event_name>.+)/$', delete_event, name='delete_event'),
    url(r'^payed-status/(?P<event_name>.+)/(?P<active_filter>.+)/$', change_visitor_payed_status, name='change_visitor_payed_status'),
    url(r'^subdomain-check/$', subdomain_check, name='subdomain_check'),
    url(r'^card-designer-save/$', save_card_outlook, name='save_card_outlook')
    ]
