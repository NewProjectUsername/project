from django.db import models
from django.conf import settings

from Event.models import Lecture, Event
from Visitor.models import EventProfile


class UhfTime(models.Model):
	user = models.ForeignKey(EventProfile)
	event = models.ForeignKey(Event)
	lecture = models.ForeignKey(Lecture,
								related_name='Lecture_rel',
                                blank=True, null=True)
	device_id = models.CharField(max_length=256, blank=True, null=True)
	direction = models.CharField(max_length=2, blank=True, null=True)
	time_of_sec = models.DateTimeField(blank=True, null=True)
	def __str__(self):
		return self.user.name
