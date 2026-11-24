from django.shortcuts import render

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from .forms import TicketForm
from .models import Ticket


class TicketListView(LoginRequiredMixin, ListView):
    model = Ticket
    context_object_name = "tickets"

    def get_queryset(self):
        qs = Ticket.objects.select_related("assigned_to")
        status = self.request.GET.get("status")
        category = self.request.GET.get("category")
        if status:
            qs = qs.filter(status=status)
        if category:
            qs = qs.filter(category=category)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status_choices"] = Ticket.Status.choices
        context["category_choices"] = Ticket.Category.choices
        context["selected_status"] = self.request.GET.get("status", "")
        context["selected_category"] = self.request.GET.get("category", "")
        return context


class TicketDetailView(LoginRequiredMixin, DetailView):
    model = Ticket
    context_object_name = "ticket"

    def get_queryset(self):
        return Ticket.objects.select_related("assigned_to").prefetch_related("notes")


class TicketCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Ticket
    form_class = TicketForm
    success_message = "Chamado criado com sucesso."

    def get_success_url(self):
        return reverse_lazy("ticket_detail", kwargs={"pk": self.object.pk})


class TicketUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Ticket
    form_class = TicketForm
    success_message = "Chamado atualizado."

    def get_success_url(self):
        return reverse_lazy("ticket_detail", kwargs={"pk": self.object.pk})