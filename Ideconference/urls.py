"""Ideconference URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""

from django.conf.urls import include, url
from django.contrib import admin
from django.conf.urls.static import static

import Ideconference.settings
from Ideconference.settings import STATIC_ROOT, STATIC_URL,MEDIA_URL,MEDIA_ROOT

from api.views import *

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^event/', include('Event.urls')),
    url(r'^summernote/', include('django_summernote.urls')),
    url(r'^visitor/', include('Visitor.urls')),
    url(r'^connect', connectMethod),
    url(r'^checkingData/', getCheckingData),
    url(r'^getBarLectures/', getLectures),
    url(r'^setData/', setData),
    url(r'^setUHFData/', setUHFData),
    url(r'^getEventData/', getEventData),
    url(r'^oauth/', include('social_django.urls', namespace='social')),
    url(r'GetUHFDeviceParticipants', getVisitors, name='getVisitors'),
    url(r'SetUHFDeviceParticipants', setVisitorsUHFModul, name='setVisitorsUHFModul'),
    url(r'getCheckingDataParticipant', getCheckingDataParticipant, name='getCheckingDataParticipant'),
    url(r'getNewUsrs', eventNewUsersPost, name='eventNewUsersPost'),
    url(r'^', include('Landing.urls')),
]

if Ideconference.settings.DEBUG:
    urlpatterns += static(STATIC_URL, document_root=STATIC_ROOT)
    urlpatterns += static(MEDIA_URL, document_root=MEDIA_ROOT)

