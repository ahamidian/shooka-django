from django_filters import rest_framework as filters

from app.models import Ticket


class TicketFilter(filters.FilterSet):
    class Meta:
        model = Ticket
        fields = {
            'status': ['exact'],
            'assigned_to': ['isnull'],
            'assigned_to_id': ['exact'],
        }
