# -*- coding: utf-8 -*-
from django.conf.urls import include, url

from .views import home, event_info, event_login, logout_view, search_events_view#, event_register

urlpatterns = [
                url(r'^$', home, name='home'),
                url(r'^event-info/(?P<event_name>.+)', event_info, name='event_info'),
                url(r'login/', event_login, name='login'),
                #url(r'^register/', event_register, name='register'),
                url(r'logout/', logout_view, name='logout'),

                url(r'^search/$', search_events_view, name='search_events')
               ]
