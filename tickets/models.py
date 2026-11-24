from django.conf import settings
from django.db import models

from accounts.roles import is_support


class TicketQuerySet(models.QuerySet):
    def visible_to(self, user):
        if not user.is_authenticated:
            return self.none()
        if is_support(user):
            return self
        return self.filter(requester=user)


class Ticket(models.Model):
    class Category(models.TextChoices):
        NETWORK = "REDE", "Rede/Conectividade"
        ACCESS = "ACESSO", "Acesso/Senha"
        HOSTING = "HOSPEDAGEM", "Hospedagem/Site"
        HARDWARE = "HARDWARE", "Hardware/Sistema"

    class Priority(models.TextChoices):
        LOW = "BAIXA", "Baixa"
        MEDIUM = "MEDIA", "Média"
        HIGH = "ALTA", "Alta"
        CRITICAL = "CRITICA", "Crítica"

    class Status(models.TextChoices):
        OPEN = "ABERTO", "Aberto"
        IN_PROGRESS = "N1", "Em Atendimento (N1)"
        ESCALATED = "N2", "Escalado para N2"
        RESOLVED = "RESOLVIDO", "Resolvido"

    title = models.CharField("Título", max_length=150)
    description = models.TextField("Descrição")
    category = models.CharField("Categoria", max_length=20, choices=Category.choices)
    priority = models.CharField(
        "Prioridade", max_length=10, choices=Priority.choices, default=Priority.MEDIUM
    )
    status = models.CharField(
        "Status", max_length=10, choices=Status.choices, default=Status.OPEN
    )
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Solicitante",
        on_delete=models.PROTECT,
        related_name="requested_tickets",
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Atendente",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_tickets",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    objects = TicketQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"#{self.pk} {self.title}"

    @property
    def resolution_time(self):
        if self.resolved_at:
            return self.resolved_at - self.created_at
        return None


class TicketNote(models.Model):

    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name="notes")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    from_status = models.CharField(max_length=10, choices=Ticket.Status.choices)
    to_status = models.CharField(max_length=10, choices=Ticket.Status.choices)
    text = models.TextField("Nota técnica / Diagnóstico", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]