from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from .roles import get_role

User = get_user_model()
admin.site.unregister(User)


@admin.register(User)
class HelpdeskUserAdmin(UserAdmin):
    list_display = ("username", "full_name", "email", "role", "is_active")
    list_filter = ("groups", "is_active", "is_superuser")

    @admin.display(description="Nome")
    def full_name(self, obj):
        return obj.get_full_name() or "-"

    @admin.display(description="Perfil")
    def role(self, obj):
        return get_role(obj).label