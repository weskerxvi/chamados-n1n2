from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from accounts.roles import is_support

from .forms import TicketRequestForm, TicketSupportForm, TransitionForm
from .models import Ticket
from .permissions import can_edit
from .services import available_transitions, change_status

FILTERS = (
    ("status", "Todos os status", Ticket.Status.choices),
    ("category", "Todas as categorias", Ticket.Category.choices),
    ("priority", "Todas as prioridades", Ticket.Priority.choices),
)


class TicketListView(LoginRequiredMixin, ListView):
    model = Ticket
    context_object_name = "tickets"

    def get_queryset(self):
        qs = Ticket.objects.visible_to(self.request.user).select_related(
            "requester", "assigned_to"
        )
        active = {
            name: self.request.GET[name]
            for name, _, _ in FILTERS
            if self.request.GET.get(name)
        }
        return qs.filter(**active)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_fields"] = [
            (name, placeholder, choices, self.request.GET.get(name, ""))
            for name, placeholder, choices in FILTERS
        ]
        context["is_support"] = is_support(self.request.user)
        return context


class TicketDetailView(LoginRequiredMixin, DetailView):
    model = Ticket
    context_object_name = "ticket"

    def get_queryset(self):
        return (
            Ticket.objects.visible_to(self.request.user)
            .select_related("requester", "assigned_to")
            .prefetch_related("notes__author")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["transitions"] = available_transitions(self.object, self.request.user)
        context["can_edit"] = can_edit(self.request.user, self.object)
        return context


class TicketFormMixin(LoginRequiredMixin, SuccessMessageMixin):
    model = Ticket

    def get_form_class(self):
        if is_support(self.request.user):
            return TicketSupportForm
        return TicketRequestForm

    def get_success_url(self):
        return reverse("ticket_detail", kwargs={"pk": self.object.pk})


class TicketCreateView(TicketFormMixin, CreateView):
    success_message = "Chamado criado com sucesso."

    def form_valid(self, form):
        if not is_support(self.request.user):
            form.instance.requester = self.request.user
        return super().form_valid(form)


class TicketUpdateView(TicketFormMixin, UpdateView):
    success_message = "Chamado atualizado."

    def get_queryset(self):
        return Ticket.objects.visible_to(self.request.user)

    def get_object(self, queryset=None):
        ticket = super().get_object(queryset)
        if not can_edit(self.request.user, ticket):
            raise PermissionDenied
        return ticket


class TicketTransitionView(LoginRequiredMixin, View):
    http_method_names = ["post"]

    def post(self, request, pk):
        ticket = get_object_or_404(Ticket.objects.visible_to(request.user), pk=pk)
        form = TransitionForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Ação inválida.")
        else:
            try:
                change_status(
                    ticket,
                    form.cleaned_data["target"],
                    request.user,
                    form.cleaned_data["note"],
                )
            except ValidationError as exc:
                messages.error(request, exc.messages[0])
            except PermissionDenied as exc:
                messages.error(request, str(exc))
            else:
                messages.success(request, "Status atualizado.")
        return redirect("ticket_detail", pk=ticket.pk)
