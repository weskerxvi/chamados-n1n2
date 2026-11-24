from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from accounts.roles import GROUP_NAMES, Role
from tickets.models import Ticket

User = get_user_model()
DEMO_PASSWORD = "demo12345"  # somente para desenvolvimento

DEMO_USERS = [
    ("admin", "Admin", "Sistema", Role.ADMIN),
    ("carlos", "Carlos", "Silva", Role.N1),
    ("paula", "Paula", "Souza", Role.N2),
    ("maria", "Maria", "Oliveira", Role.REQUESTER),
    ("joao", "João", "Santos", Role.REQUESTER),
]


class Command(BaseCommand):
    help = "Cria usuários de cada perfil e chamados de exemplo (idempotente)."

    def handle(self, *args, **options):
        users = {}
        for username, first, last, role in DEMO_USERS:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"first_name": first, "last_name": last},
            )
            if created:
                user.set_password(DEMO_PASSWORD)
                if role == Role.ADMIN:
                    user.is_staff = user.is_superuser = True
                user.save()
            if role in GROUP_NAMES:
                user.groups.add(Group.objects.get(name=GROUP_NAMES[role]))
            users[username] = user

        if not Ticket.objects.exists():
            samples = [
                ("maria", "Sem acesso ao e-mail", "Senha expirou.", Ticket.Category.ACCESS),
                ("maria", "Wi-Fi caindo", "Cai a cada 10 min.", Ticket.Category.NETWORK),
                ("joao", "Site fora do ar", "Erro 503 na loja.", Ticket.Category.HOSTING),
            ]
            for username, title, description, category in samples:
                Ticket.objects.create(
                    requester=users[username],
                    title=title,
                    description=description,
                    category=category,
                )

        self.stdout.write(self.style.SUCCESS(
            f"Pronto. Senha dos usuários de demo: {DEMO_PASSWORD}"
        ))