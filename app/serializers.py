from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from app.models import Ticket, User, Team, Message


class AgentSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "avatar"
        ]


class ClientSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "avatar",
        ]


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "avatar",
            "is_agent",
        ]


class TagSerializer(ModelSerializer):
    class Meta:
        model = Team
        fields = [
            "id",
            "name",
        ]


class TeamSerializer(ModelSerializer):
    class Meta:
        model = Team
        fields = [
            "id",
            "name",
        ]


class MessageSerializer(ModelSerializer):
    sender = UserSerializer()

    class Meta:
        model = Message
        fields = [
            "id",
            "sender",
            "title",
            "content",
            "creation_time",
            "is_note",
        ]


class TicketListSerializer(ModelSerializer):
    starter = ClientSerializer()
    assigned_to = AgentSerializer()
    assigned_team = TeamSerializer()

    class Meta:
        model = Ticket
        fields = [
            "id",
            "starter",
            "title",
            "creation_time",
            "status",
            "priority",
            "assigned_to",
            "assigned_team",
        ]


class TicketDetailSerializer(ModelSerializer):
    starter = ClientSerializer()
    assigned_to = AgentSerializer()
    assigned_team = TeamSerializer()
    messages = MessageSerializer(many=True)
    followers = AgentSerializer(many=True)

    class Meta:
        model = Ticket
        fields = [
            "id",
            "starter",
            "title",
            "creation_time",
            "status",
            "priority",
            "assigned_to",
            "assigned_team",
            "tags",
            "messages",
            "followers",
        ]
