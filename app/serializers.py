from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from app.models import Ticket, User, Team, Message, Company, Invitation, Client


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
        model = Client
        fields = [
            "id",
            "name",
            "email",
            "avatar",
        ]


class TagSerializer(ModelSerializer):
    class Meta:
        model = Team
        fields = [
            "id",
            "name",
        ]


class TeamSerializer(ModelSerializer):
    def create(self, validated_data):
        user = self.context['request'].user
        team = Team.objects.create(
            name=validated_data["name"],
            company=user.company
        )
        return team

    class Meta:
        model = Team
        fields = [
            "id",
            "name",
        ]


class MessageSerializer(ModelSerializer):
    client_sender = ClientSerializer()
    agent_sender = AgentSerializer()

    class Meta:
        model = Message
        fields = [
            "id",
            "client_sender",
            "agent_sender",
            "title",
            "content",
            "creation_time",
            "is_note",
        ]


class TicketListSerializer(ModelSerializer):
    client = ClientSerializer()
    assigned_to = AgentSerializer()
    assigned_team = TeamSerializer()

    class Meta:
        model = Ticket
        fields = [
            "id",
            "client",
            "title",
            "creation_time",
            "status",
            "priority",
            "assigned_to",
            "assigned_team",
        ]


class TicketDetailSerializer(ModelSerializer):
    client = ClientSerializer()
    assigned_to = AgentSerializer()
    assigned_team = TeamSerializer()
    messages = MessageSerializer(many=True)
    followers = AgentSerializer(many=True)

    class Meta:
        model = Ticket
        fields = [
            "id",
            "client",
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


class AdminSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    company_name = serializers.CharField(write_only=True)

    def create(self, validated_data):
        company = Company.objects.create(name=validated_data["company_name"])
        user = User.objects.create(
            username=validated_data["email"],
            email=validated_data["email"],
            company=company
        )
        if validated_data.__contains__("first_name"):
            user.first_name = validated_data["first_name"]

        if validated_data.__contains__("last_name"):
            user.first_name = validated_data["last_name"]

        user.set_password(validated_data["password"])
        user.save()
        return user

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "password",
            "first_name",
            "last_name",
            "company",
            "company_name"
        ]
        read_only_fields = ('id', 'company')


class InvitationSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        user = self.context['request'].user
        invitation = Invitation.objects.create(
            email=validated_data["email"],
            inviter=user,
            company=user.company
        )
        return invitation

    class Meta:
        model = Invitation
        fields = [
            "id",
            "email",
            "inviter",
            "company",
        ]
        read_only_fields = ('id', 'inviter', 'company')
