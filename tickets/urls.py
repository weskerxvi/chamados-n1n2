from django.urls import path

from . import views

urlpatterns = [
    path("", views.TicketListView.as_view(), name="ticket_list"),
    path("tickets/novo/", views.TicketCreateView.as_view(), name="ticket_create"),
    path("tickets/<int:pk>/", views.TicketDetailView.as_view(), name="ticket_detail"),
    path("tickets/<int:pk>/editar/", views.TicketUpdateView.as_view(), name="ticket_update"),
]