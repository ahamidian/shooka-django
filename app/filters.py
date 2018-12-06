from django.db.models import Case, When , Max
from django_filters import rest_framework as filters

from app.models import Ticket, Message


class TicketOrderingFilter(filters.OrderingFilter):

    def __init__(self, *args, **kwargs):
        super(TicketOrderingFilter, self).__init__(*args, **kwargs)
        self.extra["choices"] += [
            ('date_of_last_reply', 'date_of_last_reply'),
            ('-date_of_last_reply', 'date_of_last_reply (descending)'),
        ]

    def filter(self, qs, value):
        if value == ['date_of_last_reply']:
            tickets = Message.objects.values("ticket").annotate(Max("creation_time")).order_by(
                "creation_time__max").values(
                "ticket")

            tickets_id = []
            for value in tickets:
                tickets_id.append(value["ticket"])

            preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(tickets_id)])

            return Ticket.objects.filter(pk__in=tickets_id).order_by(preserved)

        if value == ['-date_of_last_reply']:
            tickets = Message.objects.values("ticket").annotate(Max("creation_time")).order_by(
                "-creation_time__max").values(
                "ticket")
            tickets_id = []
            for value in tickets:
                tickets_id.append(value["ticket"])

            preserved = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(tickets_id)])

            return Ticket.objects.filter(pk__in=tickets_id).order_by(preserved)
        return super(TicketOrderingFilter, self).filter(qs, value)


class TicketFilter(filters.FilterSet):
    my = filters.BooleanFilter(method='my_ticket_filter')
    unassigned = filters.BooleanFilter(method='unassigned_ticket_filter')

    order_by_field = 'ordering'
    ordering = TicketOrderingFilter(
        # fields(('model field name', 'parameter name'),)
        fields=(
            ('priority', 'priority'),
            ('creation_time', 'creation_time'),
        )
    )

    class Meta:
        model = Ticket
        fields = {
            'status': ['exact'],
            'assigned_to': ['isnull'],
            'assigned_to_id': ['exact'],
            "my": ['exact'],
            "unassigned": ['exact'],
        }

    def my_ticket_filter(self, queryset, name, value):
        agent = self.request.user
        return queryset.filter(**{'assigned_to': agent})

    def unassigned_ticket_filter(self, queryset, name, value):
        return queryset.filter(**{'assigned_to': None})
