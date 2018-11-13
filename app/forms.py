from django import forms
from django_summernote.widgets import SummernoteWidget, SummernoteInplaceWidget

from app.models import Message, Ticket


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ["content","is_note"]
        widgets = {
            'content': SummernoteWidget(),
        }


class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ["status", "priority", "assigned_to"]


class ProfileForm(forms.Form):
    signature = forms.CharField(widget=SummernoteWidget())

