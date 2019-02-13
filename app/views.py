import random
import string
import json

from django.contrib.auth.models import User
from django.http import JsonResponse
from django.http.response import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, \
    DestroyModelMixin
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework_simplejwt.views import TokenObtainPairView

from app.filters import TicketFilter
from app.models import Ticket, Message, Tag, User, Team, Client, Criteria, Company, SingleCriteria, CriteriaClause, \
    ClientProfile
from app.serializers import TicketDetailSerializer, TicketListSerializer, TeamSerializer, TagSerializer, \
    AdminSerializer, AgentSerializer, AgentSetPasswordSerializer, ClientSerializer, TicketCreateSerializer, \
    MessageSerializer, MyTokenObtainPairSerializer, CriteriaSerializer, TicketSplitSerializer, TicketMergeSerializer, \
    TicketNewSerializer


def generate_text(length=8):
    return ''.join([random.choice(string.ascii_lowercase) for i in range(length)])


def home(request):
    # EmailService().send_email("amirh.hamidian@gmail.com","subject","body")
    # for i in range(20):
    #     client = Client(name=generate_text(5) + "client",
    #                     email=generate_text(5) + "@gmail.com")
    #     client.save()
    #     message = Message(client_sender=client, title=generate_text(15), content=generate_text(20))
    #     message.save()
    if request.user.is_authenticated:
        return redirect("/tickets/")
    else:
        return redirect("/login/")


def create_images(request):
    for i in list(string.ascii_lowercase):
        client = Client(name=i,
                        email=generate_text(5) + "@gmail.com")
        client.save()

    Client.objects.all().delete()

    return HttpResponse("done")


def initial(request):
    if Company.objects.count() == 0:
        Company.objects.create(name="pushe")

    Criteria.objects.all().delete()
    my_tickets = Criteria.objects.create(name="My Tickets")
    i_follow = Criteria.objects.create(name="Tickets I Follow")
    my_team = Criteria.objects.create(name="My Team's Tickets")
    unassigned = Criteria.objects.create(name="Unassigned Tickets")
    all = Criteria.objects.create(name="All Tickets")

    clause_my_tickets = CriteriaClause.objects.create(criteria=my_tickets)
    clause_i_follow = CriteriaClause.objects.create(criteria=i_follow)
    clause_my_team = CriteriaClause.objects.create(criteria=my_team)
    clause_unassigned = CriteriaClause.objects.create(criteria=unassigned)
    clause_all = CriteriaClause.objects.create(criteria=all)

    single_my_tickets = SingleCriteria.objects.create(criteria_clause=clause_my_tickets, field="assigned_to",
                                                      operation="is", value="shooka_current_agent")
    single_i_follow = SingleCriteria.objects.create(criteria_clause=clause_i_follow, field="followers",
                                                    operation="is", value="shooka_current_agent")
    single_my_team = SingleCriteria.objects.create(criteria_clause=clause_my_team, field="assigned_team",
                                                   operation="is", value="shooka_current_agent_team")
    single_unassigned = SingleCriteria.objects.create(criteria_clause=clause_unassigned, field="assigned_to",
                                                      operation="isnull", value="True", value_type="boolean")
    single_all = SingleCriteria.objects.create(criteria_clause=clause_all, field="pk",
                                               operation="isnull", value="", value_type="boolean")

    if User.objects.count() <= 1:
        user = User.objects.create(first_name="amirhossein", email="amirh.hamidian@gmail.com",
                                   username="amirh.hamidian@gmail.com", company=Company.objects.first())
        user.set_password("123123")
        user.save()

    Client.objects.all().delete()
    Message.objects.all().delete()
    Ticket.objects.all().delete()

    for i in range(100):
        client_profile=ClientProfile(name=generate_text(5) + "client")
        client_profile.save()
        client = Client(profile=client_profile,
                        email=generate_text(5) + "@gmail.com")
        client.save()
        message = Message(client_sender=client, title=generate_text(15), content='<p>' + generate_text(20) + '</p>')
        message.save()
    return HttpResponse("done")


@csrf_exempt
def filterr(request):
    json_data = json.loads(request.body)

    criteria = SingleCriteria.objects.create(field=json_data["field"], operation=json_data["operator"],
                                             value=json_data["value"])
    tickets = []
    # for ticket in Ticket.objects.all():
    #     if criteria.is_valid_for(ticket):
    #         tickets.append(ticket.title)
    atickets = Ticket.objects.filter(criteria.get_query()).all()
    for ticket in atickets:
        tickets.append(ticket.title)

    return JsonResponse({"tickets": tickets})


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class TicketViewSet(GenericViewSet, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, ListModelMixin):
    queryset = Ticket.objects.all()
    permission_classes = [IsAuthenticated]
    filterset_class = TicketFilter

    def get_permissions(self):
        if self.action == "new":
            return [permission() for permission in [AllowAny]]
        return [permission() for permission in self.permission_classes]

    def get_queryset(self):
        return self.queryset.filter(company=self.request.user.company).order_by("-priority")

    @action(detail=False, methods=['post'])
    def split(self, request):
        serializer = TicketSplitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ticket = serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=False, methods=['post'])
    def merge(self, request):
        serializer = TicketMergeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ticket = serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK, headers=headers)

    @action(detail=False, methods=['post'])
    def new(self, request):
        serializer = TicketNewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ticket = serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=['get'])
    def filter(self, request, pk):
        criteria = get_object_or_404(Criteria, pk=pk)
        queryset = self.filter_queryset(self.get_queryset().filter(criteria.get_query(request.user)))

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = TicketListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = TicketListSerializer(queryset, many=True)
        return Response(serializer.data)

    def get_serializer_class(self, *args, **kwargs):
        if self.action == "list":
            return TicketListSerializer
        elif self.action == "create" or self.action == "partial_update":
            return TicketCreateSerializer
        else:
            return TicketDetailSerializer


class MessageViewSet(GenericViewSet, CreateModelMixin, UpdateModelMixin):
    queryset = Message.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(company=self.request.user.company)

    def get_serializer_class(self, *args, **kwargs):
        return MessageSerializer


class AgentViewSet(GenericViewSet, ListModelMixin, CreateModelMixin, UpdateModelMixin, RetrieveModelMixin,
                   DestroyModelMixin):
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(company=self.request.user.company)

    def get_serializer_class(self, *args, **kwargs):
        if self.action == "invite":
            return AgentSerializer
        else:
            return AgentSerializer


class ClientViewSet(GenericViewSet, ListModelMixin, CreateModelMixin, UpdateModelMixin, RetrieveModelMixin,
                    DestroyModelMixin):
    queryset = Client.objects.all()
    permission_classes = [IsAuthenticated]

    # @action(detail=False, methods=['post'])
    # def search(self, request):
    #     serializer = UserSearchSerializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #     ticket = serializer.save()
    #     headers = self.get_success_headers(serializer.data)
    #     return Response(serializer.data, status=status.HTTP_200_OK, headers=headers)

    def get_serializer_class(self, *args, **kwargs):
        return ClientSerializer


class TeamViewSet(GenericViewSet, ListModelMixin, CreateModelMixin, RetrieveModelMixin, UpdateModelMixin,
                  DestroyModelMixin):
    queryset = Team.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(company=self.request.user.company)

    def get_serializer_class(self, *args, **kwargs):
        return TeamSerializer


class TagViewSet(GenericViewSet, ListModelMixin):
    queryset = Tag.objects.all()
    permission_classes = [AllowAny]

    def get_queryset(self):
        return self.queryset.filter(company=self.request.user.company)

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

    @action(detail=False, methods=['post'])
    def agent(self, request, *args, **kwargs):
        serializer = AgentSetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_serializer_class(self, *args, **kwargs):
        return AgentSerializer


class CriteriaViewSet(GenericViewSet, ListModelMixin, CreateModelMixin, UpdateModelMixin, RetrieveModelMixin,
                      DestroyModelMixin):
    queryset = Criteria.objects.all()
    permission_classes = [AllowAny]

    def get_serializer_class(self, *args, **kwargs):
        return CriteriaSerializer
