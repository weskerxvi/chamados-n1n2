from dataclasses import dataclass

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from accounts.roles import Role, get_role

from .models import Ticket, TicketNote

S = Ticket.Status


@dataclass(frozen=True)
class Transition:
    source: str
    target: str
    label: str
    roles: frozenset
    requires_note: bool = False


TRANSITIONS = (
    Transition(S.OPEN, S.IN_PROGRESS, "Assumir chamado",
               frozenset({Role.N1, Role.ADMIN})),
    Transition(S.IN_PROGRESS, S.ESCALATED, "Escalar para N2",
               frozenset({Role.N1, Role.ADMIN}), requires_note=True),
    Transition(S.IN_PROGRESS, S.RESOLVED, "Resolver",
               frozenset({Role.N1, Role.ADMIN}), requires_note=True),
    Transition(S.ESCALATED, S.RESOLVED, "Resolver (N2)",
               frozenset({Role.N2, Role.ADMIN}), requires_note=True),
)


def available_transitions(ticket, user):
    """Ações que este usuário pode executar neste chamado agora."""
    role = get_role(user)
    return [t for t in TRANSITIONS if t.source == ticket.status and role in t.roles]


@transaction.atomic
def change_status(ticket, target, user, note=""):
    transition = next(
        (t for t in TRANSITIONS if t.source == ticket.status and t.target == target),
        None,
    )
    if transition is None:
        raise ValidationError("Transição de status inválida.")
    if get_role(user) not in transition.roles:
        raise PermissionDenied("Seu perfil não pode executar esta ação.")

    note = note.strip()
    if transition.requires_note and not note:
        raise ValidationError("Nota técnica obrigatória para esta ação.")

    TicketNote.objects.create(
        ticket=ticket,
        author=user,
        from_status=ticket.status,
        to_status=target,
        text=note,
    )

    ticket.status = target
    if target == S.IN_PROGRESS:
        ticket.assigned_to = user
    elif target == S.ESCALATED:
        ticket.assigned_to = None     
    elif target == S.RESOLVED:
        ticket.assigned_to = user
        ticket.resolved_at = timezone.now()
    ticket.save()
    return ticket