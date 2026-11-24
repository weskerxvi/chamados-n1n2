from django.contrib import admin

from .models import Ticket, TicketNote


class NoteInline(admin.TabularInline):
    model = TicketNote
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "category", "priority", "status", "created_at")
    list_filter = ("status", "priority", "category")
    search_fields = ("title", "requester")
    inlines = [NoteInline]