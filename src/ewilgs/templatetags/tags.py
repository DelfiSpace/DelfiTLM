"""Template tags used for filtering"""
from django import template
register = template.Library()

@register.simple_tag
def url_replace(request, field, value):
    """This method ensures that filtering and pagination work together.
    It copies the filtering parameters of the url and changes the page
    of the results so that the filter is not reset"""
    request_url = request.GET.copy()
    request_url[field] = value
    return request_url.urlencode()
