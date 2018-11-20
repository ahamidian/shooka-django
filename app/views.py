import random
import string

from django.contrib.auth import authenticate, login as auth_login, logout as auth_loguot
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404, redirect
from rest_framework import status
from rest_framework.decorators import api_view, action
from rest_framework.mixins import ListModelMixin, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from app.filters import TicketFilter
from app.forms import MessageForm, ProfileForm
from app.serializers import TicketDetailSerializer, TicketListSerializer, UserSerializer, TeamSerializer, TagSerializer, \
    AdminSerializer, AgentSerializer
from app.models import Ticket, Message, Tag, User, Team


def generate_text(length=8):
    return ''.join([random.choice(string.ascii_lowercase) for i in range(length)])


def home(request):
    if request.user.is_authenticated:
        return redirect("/tickets/")
    else:
        return redirect("/login/")


@login_required
def tickets_page(request):
    # for i in range(20):
    #     user = User.objects.create_user(generate_text(5) + "client",
    #                                     generate_text(5) + "@gmail.com",
    #                                     is_agent=False)
    #     Message.objects.create(sender=user, title=generate_text(15), content=generate_text(20))
    current_agent = User.objects.get(pk=request.user.pk)
    tickets = Ticket.objects.all()
    for k, vals in request.GET.lists():
        for v in vals:
            tickets = tickets.filter(**{k: v})

    return render(request, "tickets_page2.html", {"tickets": tickets, "current_agent": current_agent})


@login_required
def ticket_detail(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    current_agent = User.objects.get(pk=request.user.pk)
    agents = []
    for agent in User.objects.filter(is_agent=True):
        agents.append({"id": agent.pk, "name": agent.email,
                       "image": agent.get_avatar()})

    statuses = []
    for i in range(Ticket.STATUSES.__len__()):
        statuses.append({"id": i, "name": Ticket.STATUSES[i]})

    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            message = Message.objects.create(sender=request.user, content=form.cleaned_data["content"],
                                             is_note=form.cleaned_data["is_note"])
            ticket.messages.add(message)
            if not form.cleaned_data["is_note"]:
                ticket.status = Ticket.STATUS_AWAITING_USER
            ticket.save()

    form = MessageForm(initial={'content': current_agent.signature})

    return render(request, "tickets_detail2.html",
                  {"ticket": ticket, "form": form, "agents": agents, "teams": Team.objects.all(), "statuses": statuses,
                   "tags": Tag.objects.all(), "current_agent": current_agent})


@login_required
def submit_ticket_setting(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    current_agent = User.objects.get(pk=request.user.pk)

    if request.method == "POST":

        if request.POST["assigned_to"] != "Unassigned":
            ticket.assigned_to = User.objects.get(pk=request.POST["assigned_to"])
        else:
            ticket.assigned_to = None

        if request.POST["assigned_team"] != "Unassigned":
            ticket.assigned_team = Team.objects.get(pk=request.POST["assigned_team"])
        else:
            ticket.assigned_team = None
        ticket.priority = request.POST["priority"]
        ticket.status = request.POST["status"]
        if request.POST.get("follow", False):
            ticket.followers.add(current_agent)
        else:
            ticket.followers.remove(current_agent)

        ticket.tags.clear()
        for tag_id in request.POST.getlist("tags"):
            ticket.tags.add(Tag.objects.get(id=tag_id))

        ticket.save()

    return redirect("/ticket/" + str(pk))


@login_required
def profile(request):
    current_agent = User.objects.get(pk=request.user.pk)
    if request.method == "POST":
        form = ProfileForm(request.POST)
        if form.is_valid():
            current_agent.signature = form.cleaned_data["signature"]
            current_agent.save()

    form = ProfileForm(initial={'signature': current_agent.signature})

    return render(request, "profile.html", {"form": form, "current_agent": current_agent})


@login_required
def user_detail(request, pk):
    client = get_object_or_404(User, pk=pk, is_agent=False)
    current_agent = User.objects.get(pk=request.user.pk)
    agents = []

    client_tickets = Ticket.objects.filter(starter=client)
    return render(request, "user_detail.html",
                  {"client_tickets": client_tickets, "current_agent": current_agent})


def login(request):
    if request.user.is_authenticated:
        return redirect("/tickets/")

    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect("/tickets/")

    return render(request, "login.html", {})


def register(request):
    if request.user.is_authenticated:
        return redirect("/tickets/")

    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        password2 = request.POST['password2']
        if password == password2:
            agent = User.objects.create_user(username=username, password=password, is_agent=True)
            auth_login(request, agent)
            return redirect("/tickets/")

    return render(request, "register.html", {})


def logout(request):
    auth_loguot(request)
    return redirect("/")


class TicketViewSet(GenericViewSet, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, ListModelMixin):
    queryset = Ticket.objects.all()
    permission_classes = [AllowAny]
    # filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = TicketFilter

    def get_queryset(self):
        return self.queryset.filter()

    def get_serializer_class(self, *args, **kwargs):
        if self.action == "list":
            return TicketListSerializer
        else:
            return TicketDetailSerializer


class AgentViewSet(GenericViewSet, ListModelMixin):
    queryset = User.objects.filter(is_agent=True)
    permission_classes = [AllowAny]

    def get_serializer_class(self, *args, **kwargs):
        if self.action == "list":
            return UserSerializer


class TeamViewSet(GenericViewSet, ListModelMixin):
    queryset = Team.objects.all()
    permission_classes = [AllowAny]

    def get_serializer_class(self, *args, **kwargs):
        if self.action == "list":
            return TeamSerializer


class TagViewSet(GenericViewSet, ListModelMixin):
    queryset = Tag.objects.all()
    permission_classes = [AllowAny]

    def get_serializer_class(self, *args, **kwargs):
        if self.action == "list":
            return TagSerializer


class RegisterViewSet(GenericViewSet, CreateModelMixin):
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'])
    def admin(self, request, *args, **kwargs):
        serializer = AdminSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_serializer_class(self, *args, **kwargs):
            return AgentSerializer
