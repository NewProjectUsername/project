from django import template
from django.utils import timezone

register = template.Library()

@register.filter
def inprogress(lecture):
    if lecture.start_time < timezone.now() and lecture.end_time > timezone.now():
        return True
    else:
        return False

@register.filter
def finished(lecture):
    if lecture.start_time < timezone.now() and lecture.end_time < timezone.now():
        return True
    else:
        return False