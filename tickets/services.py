from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from .models import Ticket, TicketNote

ALLOWED_TRANSITIONS = {
    Ticket.Status.OPEN: {Ticket.Status.IN_PROGRESS},
    Ticket.Status.IN_PROGRESS: {Ticket.Status.ESCALATED, Ticket.Status.RESOLVED},
    Ticket.Status.ESCALATED: {Ticket.Status.RESOLVED},
    Ticket.Status.RESOLVED: set(),
}
NOTE_REQUIRED = {Ticket.Status.ESCALATED, Ticket.Status.RESOLVED}


@transaction.atomic
def change_status(ticket, new_status, user, note=""):
    if new_status not in ALLOWED_TRANSITIONS[ticket.status]:
        raise ValidationError(
            f"Transição inválida: {ticket.get_status_display()} → {new_status}"
        )
    if new_status in NOTE_REQUIRED and not note.strip():
        raise ValidationError("Nota técnica obrigatória para escalar ou resolver.")

    TicketNote.objects.create(
        ticket=ticket, author=user,
        from_status=ticket.status, to_status=new_status, text=note,
    )
    ticket.status = new_status
    if new_status == Ticket.Status.IN_PROGRESS:
        ticket.assigned_to = user
    if new_status == Ticket.Status.RESOLVED:
        ticket.resolved_at = timezone.now()
    ticket.save()
    return ticket