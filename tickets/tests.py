from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from accounts.roles import Role
from .models import Ticket, TicketNote

User = get_user_model()


class TicketWorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.requester = User.objects.create_user("ana", password="test-pass-123")
        cls.other_requester = User.objects.create_user("bia", password="test-pass-123")
        cls.agent = User.objects.create_user("n1", password="test-pass-123")
        cls.agent.groups.add(Group.objects.get(name="Suporte N1"))
        cls.ticket = Ticket.objects.create(
            title="Sem acesso", description="Não consigo entrar", category=Ticket.Category.ACCESS,
            requester=cls.requester,
        )

    def test_ticket_list_renders_with_shared_layout(self):
        self.client.force_login(self.requester)
        response = self.client.get(reverse("ticket_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<!doctype html>")
        self.assertContains(response, "Meus chamados")
        self.assertContains(response, "Sem acesso")

    def test_requester_only_sees_own_tickets(self):
        Ticket.objects.create(
            title="Outro chamado", description="Privado", category=Ticket.Category.NETWORK,
            requester=self.other_requester,
        )
        self.client.force_login(self.requester)
        response = self.client.get(reverse("ticket_list"))
        self.assertContains(response, "Sem acesso")
        self.assertNotContains(response, "Outro chamado")

    def test_requester_can_create_ticket_as_self(self):
        self.client.force_login(self.requester)
        response = self.client.post(reverse("ticket_create"), {
            "title": "Impressora", "description": "Não imprime", "category": Ticket.Category.HARDWARE,
        })
        created = Ticket.objects.get(title="Impressora")
        self.assertEqual(created.requester, self.requester)
        self.assertRedirects(response, reverse("ticket_detail", args=[created.pk]))

    def test_support_can_assign_ticket_and_transition_it(self):
        self.client.force_login(self.agent)
        response = self.client.post(reverse("ticket_transition", args=[self.ticket.pk]), {
            "target": Ticket.Status.IN_PROGRESS,
        }, follow=True)
        self.assertRedirects(response, reverse("ticket_detail", args=[self.ticket.pk]))
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, Ticket.Status.IN_PROGRESS)
        self.assertEqual(self.ticket.assigned_to, self.agent)
        self.assertEqual(TicketNote.objects.get(ticket=self.ticket).to_status, Ticket.Status.IN_PROGRESS)

    def test_transition_requiring_note_rejects_empty_note(self):
        self.ticket.status = Ticket.Status.IN_PROGRESS
        self.ticket.assigned_to = self.agent
        self.ticket.save()
        self.client.force_login(self.agent)
        self.client.post(reverse("ticket_transition", args=[self.ticket.pk]), {
            "target": Ticket.Status.RESOLVED, "note": "   ",
        })
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, Ticket.Status.IN_PROGRESS)
        self.assertFalse(TicketNote.objects.filter(ticket=self.ticket).exists())

    def test_requester_cannot_change_ticket_status(self):
        self.client.force_login(self.requester)
        response = self.client.post(reverse("ticket_transition", args=[self.ticket.pk]), {
            "target": Ticket.Status.IN_PROGRESS,
        }, follow=True)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, Ticket.Status.OPEN)
        self.assertContains(response, "Seu perfil não pode executar esta ação.")

    def test_support_filters_ticket_queue(self):
        self.client.force_login(self.agent)
        response = self.client.get(reverse("ticket_list"), {"category": Ticket.Category.ACCESS})
        self.assertContains(response, "Fila de chamados")
        self.assertContains(response, "Sem acesso")
        self.assertEqual(response.context["filter_fields"][1][3], Ticket.Category.ACCESS)
