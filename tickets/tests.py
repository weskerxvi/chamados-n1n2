from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Ticket

User = get_user_model()


def make_ticket(**overrides):
    data = {
        "title": "Sem internet",
        "description": "Computador não conecta na rede.",
        "category": Ticket.Category.NETWORK,
        "priority": Ticket.Priority.MEDIUM,
        "requester": "Maria",
    }
    data.update(overrides)
    return Ticket.objects.create(**data)


def valid_form_data(**overrides):
    data = {
        "title": "Erro de DNS",
        "description": "Sites não abrem pelo nome.",
        "category": Ticket.Category.NETWORK.value,
        "priority": Ticket.Priority.HIGH.value,
        "requester": "João",
    }
    data.update(overrides)
    return data


class TicketModelTests(TestCase):
    def test_new_ticket_starts_open(self):
        ticket = make_ticket()
        self.assertEqual(ticket.status, Ticket.Status.OPEN)
        self.assertIsNone(ticket.assigned_to)
        self.assertIsNone(ticket.resolved_at)

    def test_str_shows_id_and_title(self):
        ticket = make_ticket(title="Lentidão")
        self.assertEqual(str(ticket), f"#{ticket.pk} Lentidão")

    def test_resolution_time_is_none_while_unresolved(self):
        self.assertIsNone(make_ticket().resolution_time)

    def test_resolution_time_is_difference_between_dates(self):
        ticket = make_ticket()
        ticket.resolved_at = ticket.created_at + timedelta(hours=2)
        self.assertEqual(ticket.resolution_time, timedelta(hours=2))

    def test_default_ordering_is_newest_first(self):
        first = make_ticket(title="Primeiro")
        second = make_ticket(title="Segundo")
        self.assertEqual(list(Ticket.objects.all()), [second, first])


class AuthenticationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="ana", password="senha-forte-123")
        cls.ticket = make_ticket()

    def test_protected_pages_redirect_anonymous_to_login(self):
        urls = [
            reverse("ticket_list"),
            reverse("ticket_create"),
            reverse("ticket_detail", kwargs={"pk": self.ticket.pk}),
            reverse("ticket_update", kwargs={"pk": self.ticket.pk}),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(response, f"{reverse('login')}?next={url}")

    def test_login_page_loads(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)

    def test_login_with_valid_credentials_redirects_to_list(self):
        response = self.client.post(
            reverse("login"),
            {"username": "ana", "password": "senha-forte-123"},
        )
        self.assertRedirects(response, reverse("ticket_list"))

    def test_login_with_invalid_credentials_shows_error(self):
        response = self.client.post(
            reverse("login"),
            {"username": "ana", "password": "errada"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Usuário ou senha inválidos")

    def test_logout_via_post_redirects_to_login(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("login"))
        # depois do logout, a lista volta a exigir login
        response = self.client.get(reverse("ticket_list"))
        self.assertEqual(response.status_code, 302)


class TicketCrudTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="ana", password="senha-forte-123")

    def setUp(self):
        self.client.force_login(self.user)

    # --- create ---
    def test_create_page_loads(self):
        response = self.client.get(reverse("ticket_create"))
        self.assertEqual(response.status_code, 200)

    def test_create_with_valid_data_saves_and_redirects_to_detail(self):
        response = self.client.post(reverse("ticket_create"), valid_form_data())
        ticket = Ticket.objects.get()
        self.assertRedirects(
            response, reverse("ticket_detail", kwargs={"pk": ticket.pk})
        )
        self.assertEqual(ticket.title, "Erro de DNS")
        self.assertEqual(ticket.status, Ticket.Status.OPEN)

    def test_create_with_missing_title_shows_errors_and_saves_nothing(self):
        response = self.client.post(reverse("ticket_create"), valid_form_data(title=""))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
        self.assertEqual(Ticket.objects.count(), 0)

    def test_create_with_invalid_category_is_rejected(self):
        response = self.client.post(
            reverse("ticket_create"), valid_form_data(category="INEXISTENTE")
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Ticket.objects.count(), 0)

    def test_create_ignores_status_sent_in_post(self):
        self.client.post(reverse("ticket_create"), valid_form_data(status="RESOLVIDO"))
        self.assertEqual(Ticket.objects.get().status, Ticket.Status.OPEN)

    def test_detail_shows_ticket_data(self):
        ticket = make_ticket(title="Impressora travada", requester="Carlos")
        response = self.client.get(reverse("ticket_detail", kwargs={"pk": ticket.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Impressora travada")
        self.assertContains(response, "Carlos")

    def test_detail_returns_404_for_unknown_ticket(self):
        response = self.client.get(reverse("ticket_detail", kwargs={"pk": 9999}))
        self.assertEqual(response.status_code, 404)

    def test_update_changes_fields_and_keeps_status(self):
        ticket = make_ticket()
        response = self.client.post(
            reverse("ticket_update", kwargs={"pk": ticket.pk}),
            valid_form_data(title="Título novo", priority=Ticket.Priority.CRITICAL.value),
        )
        self.assertRedirects(
            response, reverse("ticket_detail", kwargs={"pk": ticket.pk})
        )
        ticket.refresh_from_db()
        self.assertEqual(ticket.title, "Título novo")
        self.assertEqual(ticket.priority, Ticket.Priority.CRITICAL)
        self.assertEqual(ticket.status, Ticket.Status.OPEN)

    def test_update_with_invalid_data_does_not_change_ticket(self):
        ticket = make_ticket(title="Original")
        self.client.post(
            reverse("ticket_update", kwargs={"pk": ticket.pk}),
            valid_form_data(title=""),
        )
        ticket.refresh_from_db()
        self.assertEqual(ticket.title, "Original")


class TicketListFilterTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="ana", password="senha-forte-123")
        cls.net_open = make_ticket(title="Rede aberta")
        cls.net_n1 = make_ticket(title="Rede em N1", status=Ticket.Status.IN_PROGRESS)
        cls.hw_open = make_ticket(
            title="Hardware aberto", category=Ticket.Category.HARDWARE
        )

    def setUp(self):
        self.client.force_login(self.user)

    def titles(self, **params):
        response = self.client.get(reverse("ticket_list"), params)
        self.assertEqual(response.status_code, 200)
        return {t.title for t in response.context["tickets"]}

    def test_list_without_filters_shows_all(self):
        self.assertEqual(
            self.titles(), {"Rede aberta", "Rede em N1", "Hardware aberto"}
        )

    def test_filter_by_status(self):
        self.assertEqual(
            self.titles(status=Ticket.Status.IN_PROGRESS.value), {"Rede em N1"}
        )

    def test_filter_by_category(self):
        self.assertEqual(
            self.titles(category=Ticket.Category.HARDWARE.value), {"Hardware aberto"}
        )

    def test_filter_by_status_and_category_combined(self):
        result = self.titles(
            status=Ticket.Status.OPEN.value,
            category=Ticket.Category.NETWORK.value,
        )
        self.assertEqual(result, {"Rede aberta"})

    def test_filter_with_no_match_shows_empty_message(self):
        response = self.client.get(
            reverse("ticket_list"), {"status": Ticket.Status.RESOLVED.value}
        )
        self.assertContains(response, "Nenhum chamado encontrado")