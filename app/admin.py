from django.contrib import admin
from app.models import Ticket, Tag, Message, User, Team, Filter, Company

admin.site.register(Ticket)
admin.site.register(Message)
admin.site.register(Tag)
admin.site.register(User)
admin.site.register(Team)
admin.site.register(Filter)
admin.site.register(Company)
