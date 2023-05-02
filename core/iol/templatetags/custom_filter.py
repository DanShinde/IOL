from django import template

register = template.Library()

@register.filter
def split_string(value, arg):
    return value.split(arg)
