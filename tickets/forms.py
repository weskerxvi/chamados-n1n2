from django import forms
from django.contrib.auth import get_user_model

from accounts.roles import display_name

from .models import Ticket

User = get_user_model()


class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            is_select = isinstance(field.widget, forms.Select)
            field.widget.attrs["class"] = "form-select" if is_select else "form-control"


class TicketRequestForm(BootstrapFormMixin, forms.ModelForm):

    class Meta:
        model = Ticket
        fields = ["title", "description", "category"]
        widgets = {"description": forms.Textarea(attrs={"rows": 5})}


class TicketSupportForm(TicketRequestForm):

    class Meta(TicketRequestForm.Meta):
        fields = ["title", "description", "category", "priority", "requester"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        requester = self.fields["requester"]
        requester.queryset = User.objects.filter(is_active=True).order_by(
            "first_name", "username"
        )
        requester.label_from_instance = display_name


class TransitionForm(forms.Form):
    target = forms.ChoiceField(choices=Ticket.Status.choices)
    note = forms.CharField(required=False)