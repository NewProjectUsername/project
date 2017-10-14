from django import template

register = template.Library()

@register.filter
def sorted_fields(entry, selected):
    return [entry[key] for key in selected]