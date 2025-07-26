from django import template

register = template.Library()

@register.filter
def stars_range(arg):
    return range(10, 0, -1)

@register.filter
def adjust(value):
    return (int(value) - 1) / 2

@register.filter
def make_range(start, end):
    return range(start, end + 1)

@register.filter
def split_by_comma(value):
    return [item.strip() for item in value.split(',')] if value else []

@register.filter
def split_by_newline(value):
    """Split text into lines for use in <li> loops"""
    return value.splitlines()