from django import template

register = template.Library()

@register.simple_tag
def update_query(request, **kwargs):
    data = request.GET.copy()
    for key, value in kwargs.items():
        if value in (None, ''):
            data.pop(key, None)
        else:
            data[key] = value
    return data.urlencode()
