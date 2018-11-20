from io import BytesIO, StringIO

from PIL.ImageColor import getrgb
from django.contrib.auth.models import AbstractUser
from django.core.files.base import ContentFile
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import SET_NULL, CASCADE
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFont


class User(AbstractUser):
    avatar = models.ImageField(upload_to="avatar/", null=True, blank=True)
    is_agent = models.NullBooleanField(null=True, blank=True)
    team = models.ForeignKey("Team", on_delete=SET_NULL, null=True, blank=True)
    signature = models.TextField(default="", blank=True, null=True)
    company = models.ForeignKey("Company", on_delete=CASCADE, null=True, blank=True)

    def get_avatar(self):
        if self.avatar:
            return "http://127.0.0.1:8000" + self.avatar.url
        return None

    def save(self, *args, **kwargs):
        if not self.avatar:
            colors = [
                "#1abc9c", "#2ecc71", "#3498db", "#9b59b6", "#34495e", "#16a085", "#27ae60", "#2980b9", "#8e44ad",
                "#2c3e50",
                "#f1c40f", "#e67e22", "#e74c3c", "#ecf0f1", "#95a5a6", "#f39c12", "#d35400", "#c0392b", "#bdc3c7",
                "#7f8c8d"
            ]
            img = Image.new('RGB', (64, 64), getrgb(colors[ord(self.username[0].upper()) % 20]))
            img_io = BytesIO()
            # font = ImageFont.truetype('/Library/Fonts/Arial.ttf', 35)
            draw = ImageDraw.Draw(img)
            # w, h = draw.textsize(self.username[0].upper(), font=font)
            # draw.text(((64 - w) / 2, (54 - h) / 2), self.username[0].upper(), font=font, fill=(255, 255, 255))
            img.save(img_io, format='PNG', quality=100)
            self.avatar = ContentFile(img_io.getvalue(), 'image.png')
        super(User, self).save(*args, **kwargs)


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
    sender = models.ForeignKey(User, on_delete=SET_NULL, null=True)
    title = models.CharField(max_length=255, default="no subject")
    content = models.TextField()
    creation_time = models.DateTimeField(default=timezone.now)
    is_note = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    def is_agent_message(self):
        return self.sender.is_agent

    def save(self, *args, **kwargs):
        super(Message, self).save(*args, **kwargs)
        if not self.is_agent_message():
            if Ticket.objects.filter(starter_id=self.sender.id, status=Ticket.STATUS_AWAITING_USER).exists():
                ticket = Ticket.objects.get(starter_id=self.sender.id, status=Ticket.STATUS_AWAITING_USER)
            else:
                ticket = Ticket.objects.create(starter=self.sender, title=self.title)
            ticket.messages.add(self)


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

    starter = models.ForeignKey(User, on_delete=CASCADE, null=True, blank=True, related_name="starter")
    title = models.CharField(max_length=255, default="no subject")
    creation_time = models.DateTimeField(default=timezone.now)
    status = models.IntegerField(choices=STATUS_CHOICES, default=STATUS_AWAITING_AGENT)
    priority = models.SmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)], default=1)
    tags = models.ManyToManyField(Tag)
    messages = models.ManyToManyField(Message)
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
    email = models.EmailField()
    creation_time = models.DateTimeField(default=timezone.now)
    inviter = models.ForeignKey(User, on_delete=SET_NULL, null=True)
    company = models.ForeignKey("Company", on_delete=CASCADE)

