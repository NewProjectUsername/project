from django import template

register = template.Library()

@register.filter
def field_by_key(form, field):
    return form.__getitem__(field)