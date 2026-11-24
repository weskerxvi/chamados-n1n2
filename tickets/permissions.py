from accounts.roles import is_support

from .models import Ticket


def can_view(user, ticket):
    return is_support(user) or ticket.requester_id == user.id


def can_edit(user, ticket):
    if ticket.status == Ticket.Status.RESOLVED:
        return False
    if is_support(user):
        return True
    return ticket.requester_id == user.id and ticket.status == Ticket.Status.OPEN