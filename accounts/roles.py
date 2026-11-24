from django.db.models import TextChoices


class Role(TextChoices):
    ADMIN = "ADMIN", "Administrador"
    N2 = "N2", "Suporte N2"
    N1 = "N1", "Suporte N1"
    REQUESTER = "REQUESTER", "Solicitante"


GROUP_NAMES = {
    Role.N2: "Suporte N2",
    Role.N1: "Suporte N1",
    Role.REQUESTER: "Solicitante",
}


def get_role(user):
    if not user.is_authenticated:
        return None
    if user.is_superuser:
        return Role.ADMIN
    names = set(user.groups.values_list("name", flat=True))
    if GROUP_NAMES[Role.N2] in names:
        return Role.N2
    if GROUP_NAMES[Role.N1] in names:
        return Role.N1
    return Role.REQUESTER


def is_support(user):
    return get_role(user) in {Role.ADMIN, Role.N1, Role.N2}


def display_name(user):
    return user.get_full_name() or user.get_username()