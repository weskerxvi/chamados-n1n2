from .roles import get_role, is_support


def role(request):
    return {
        "current_role": get_role(request.user),
        "is_support": is_support(request.user),
    }