from io import BytesIO, StringIO

from PIL.ImageColor import getrgb
from django.contrib.auth.models import AbstractUser
from django.core.files.base import ContentFile
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import SET_NULL, CASCADE
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFont
from django.utils.crypto import get_random_string
import operator


class User(AbstractUser):
    avatar = models.ImageField(upload_to="avatar/", null=True, blank=True)
    teams = models.ManyToManyField("Team", blank=True)
    signature = models.TextField(default="", blank=True, null=True)
    company = models.ForeignKey("Company", on_delete=CASCADE, null=True, blank=True)
    invitation = models.ForeignKey("Invitation", on_delete=CASCADE, null=True, blank=True)
    phone_number = models.CharField(max_length=11, null=True, blank=True)

    def get_avatar(self):
        if self.avatar:
            return "http://127.0.0.1:8000" + self.avatar.url
        return None

    def save(self, *args, **kwargs):
        if not self.avatar:
            self.avatar = "avatar/image_" + self.username[0].lower() + ".png"
        super(User, self).save(*args, **kwargs)


class Client(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    avatar = models.ImageField(upload_to="avatar/", null=True, blank=True)
    company = models.ForeignKey("Company", on_delete=CASCADE, null=True, blank=True)

    def get_avatar(self):
        if self.avatar:
            return "http://127.0.0.1:8000" + self.avatar.url
        return None

    def save(self, *args, **kwargs):
        if not self.avatar:
            self.avatar = "avatar/image_" + self.name[0].lower() + ".png"
            # colors = [
            #     "#1abc9c", "#2ecc71", "#3498db", "#9b59b6", "#34495e", "#16a085", "#27ae60", "#2980b9", "#8e44ad",
            #     "#f1c40f", "#e67e22", "#e74c3c", "#f39c12", "#d35400", "#c0392b",
            # ]
            # img = Image.new('RGB', (64, 64), getrgb(colors[ord(self.name[0].upper()) % 15]))
            # img_io = BytesIO()
            # font = ImageFont.truetype('../arial.ttf', 35)
            # draw = ImageDraw.Draw(img)
            # w, h = draw.textsize(self.name[0].upper(), font=font)
            # draw.text(((64 - w) / 2, (54 - h) / 2), self.name[0].upper(), font=font, fill=(255, 255, 255))
            # img.save(img_io, format='PNG', quality=100)
            # self.avatar = ContentFile(img_io.getvalue(), 'image_'+self.name[0].upper()+'.png')
        super(Client, self).save(*args, **kwargs)


class Tag(models.Model):
    name = models.CharField(max_length=255)
    creation_time = models.DateTimeField(default=timezone.now)
    company = models.ForeignKey("Company", on_delete=CASCADE)

    def __str__(self):
        return self.name


class Team(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False)
    company = models.ForeignKey("Company", on_delete=CASCADE)

    def __str__(self):
        return self.name


class Message(models.Model):
    client_sender = models.ForeignKey(Client, on_delete=SET_NULL, null=True, blank=True)
    agent_sender = models.ForeignKey(User, on_delete=SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=255, default="no subject")
    content = models.TextField()
    creation_time = models.DateTimeField(default=timezone.now)
    is_note = models.BooleanField(default=False)
    ticket = models.ForeignKey("Ticket", on_delete=CASCADE, null=True, blank=True)

    def __str__(self):
        return self.title

    def is_agent_message(self):
        return self.agent_sender is not None

    def save(self, *args, **kwargs):
        if not self.is_agent_message():
            if Ticket.objects.filter(client_id=self.client_sender.id, status=Ticket.STATUS_AWAITING_USER).exists():
                ticket = Ticket.objects.get(client_id=self.client_sender.id, status=Ticket.STATUS_AWAITING_USER)
            else:
                ticket = Ticket.objects.create(client=self.client_sender, title=self.title,
                                               company=Company.objects.first())
            self.ticket = ticket
        super(Message, self).save(*args, **kwargs)


class Ticket(models.Model):
    STATUS_AWAITING_USER = 0
    STATUS_AWAITING_AGENT = 1
    STATUS_RESOLVED = 2
    STATUS_CHOICES = (
        (STATUS_AWAITING_USER, "Awaiting user"),
        (STATUS_AWAITING_AGENT, "Awaiting agent"),
        (STATUS_RESOLVED, "Resolved"),
    )
    STATUSES = {k: v for (k, v) in STATUS_CHOICES}

    client = models.ForeignKey(Client, on_delete=CASCADE, null=True, blank=True, related_name="starter")
    title = models.CharField(max_length=255, default="no subject")
    creation_time = models.DateTimeField(default=timezone.now)
    status = models.IntegerField(choices=STATUS_CHOICES, default=STATUS_AWAITING_AGENT)
    priority = models.SmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)], default=1)
    tags = models.ManyToManyField(Tag, blank=True)
    assigned_to = models.ForeignKey(User, on_delete=SET_NULL, null=True, related_name="assigned_to")
    assigned_team = models.ForeignKey(Team, on_delete=SET_NULL, null=True)
    followers = models.ManyToManyField(User, related_name="follows")
    company = models.ForeignKey("Company", on_delete=CASCADE)

    def __str__(self):
        return self.title

    def get_status_name(self):
        return self.STATUSES.get(self.status)


class Filter(models.Model):
    name = models.CharField(max_length=255)
    query = models.CharField(max_length=1023)
    agent = models.ForeignKey(User, on_delete=CASCADE)

    def __str__(self):
        return self.name


class Company(models.Model):
    name = models.CharField(max_length=255)
    creation_time = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name


class Invitation(models.Model):
    creation_time = models.DateTimeField(default=timezone.now)
    inviter = models.ForeignKey(User, on_delete=SET_NULL, null=True, related_name="inviter")
    key = models.CharField(max_length=64)

    def save(self, *args, **kwargs):
        self.key = get_random_string(64).lower()
        super(Invitation, self).save(*args, **kwargs)


class Criteria(models.Model):
    name = models.CharField(max_length=255)

    def is_valid_for(self, ticket):
        for criteria_clause in self.clauses.all():
            if criteria_clause.is_valid_for(ticket):
                return True

        return False


class CriteriaClause(models.Model):
    criteria = models.ForeignKey(Criteria, on_delete=CASCADE, related_name="clauses")

    def is_valid_for(self, ticket):
        for single_criteria in self.singles.all():
            if not single_criteria.is_valid_for(ticket):
                return False

        return True


class SingleCriteria(models.Model):
    field = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
    value_type = models.CharField(max_length=255)
    operation = models.CharField(max_length=255)
    criteria_clause = models.ForeignKey(CriteriaClause, on_delete=CASCADE, related_name="singles")

    def is_valid_for(self, ticket):
        if not hasattr(ticket, self.field):
            return False

        ticket_value = operator.attrgetter(self.field)(ticket)
        value = self.value
        if self.value_type == "int":
            value = int(self.value)

        if self.operation == "is":
            return ticket_value == value
        if self.operation == "is not":
            return ticket_value != value
        if self.operation == "grater than":
            return ticket_value > value
        if self.operation == "less than":
            return ticket_value < value
        if self.operation == "contains":
            return value in ticket_value
        if self.operation == "not contains":
            return value not in ticket_value

        return False
