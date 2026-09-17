from .utils import get_user_role

def navigation_context(request):
    return {
        'nav_role': get_user_role(request.user) if request.user.is_authenticated else '',
    }
