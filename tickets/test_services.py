from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from .models import Ticket, TicketNote
from .services import change_status

User = get_user_model()


class ChangeStatusTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="ana", password="senha-forte-123")

    def make_ticket(self, status=Ticket.Status.OPEN):
        return Ticket.objects.create(
            title="Sem acesso",
            description="Não consigo logar.",
            category=Ticket.Category.ACCESS,
            requester="Maria",
            status=status,
        )

    def test_open_to_n1_assigns_the_attendant(self):
        ticket = self.make_ticket()
        change_status(ticket, Ticket.Status.IN_PROGRESS, self.user)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, Ticket.Status.IN_PROGRESS)
        self.assertEqual(ticket.assigned_to, self.user)

    def test_escalating_requires_technical_note(self):
        ticket = self.make_ticket(Ticket.Status.IN_PROGRESS)
        with self.assertRaises(ValidationError):
            change_status(ticket, Ticket.Status.ESCALATED, self.user, note="   ")

    def test_resolving_requires_technical_note(self):
        ticket = self.make_ticket(Ticket.Status.IN_PROGRESS)
        with self.assertRaises(ValidationError):
            change_status(ticket, Ticket.Status.RESOLVED, self.user, note="")

    def test_escalating_with_note_saves_history(self):
        ticket = self.make_ticket(Ticket.Status.IN_PROGRESS)
        change_status(ticket, Ticket.Status.ESCALATED, self.user, note="DNS interno fora.")
        ticket.refresh_from_db()
        note = TicketNote.objects.get()
        self.assertEqual(ticket.status, Ticket.Status.ESCALATED)
        self.assertEqual(note.from_status, Ticket.Status.IN_PROGRESS)
        self.assertEqual(note.to_status, Ticket.Status.ESCALATED)
        self.assertEqual(note.author, self.user)

    def test_resolving_sets_resolved_at(self):
        ticket = self.make_ticket(Ticket.Status.ESCALATED)
        change_status(ticket, Ticket.Status.RESOLVED, self.user, note="Reiniciado serviço.")
        ticket.refresh_from_db()
        self.assertIsNotNone(ticket.resolved_at)

    def test_invalid_transition_is_rejected(self):
        ticket = self.make_ticket()  # ABERTO não pode ir direto para N2
        with self.assertRaises(ValidationError):
            change_status(ticket, Ticket.Status.ESCALATED, self.user, note="x")

    def test_resolved_ticket_cannot_be_reopened(self):
        ticket = self.make_ticket(Ticket.Status.RESOLVED)
        with self.assertRaises(ValidationError):
            change_status(ticket, Ticket.Status.IN_PROGRESS, self.user)

    def test_failed_change_leaves_no_note_and_keeps_status(self):
        ticket = self.make_ticket(Ticket.Status.IN_PROGRESS)
        with self.assertRaises(ValidationError):
            change_status(ticket, Ticket.Status.RESOLVED, self.user, note="")
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, Ticket.Status.IN_PROGRESS)
        self.assertEqual(TicketNote.objects.count(), 0)