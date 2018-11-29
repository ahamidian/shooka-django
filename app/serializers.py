from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from app.models import Ticket, User, Team, Message, Company, Invitation, Client
from app.servises import EmailService


class AgentSerializer(ModelSerializer):
    def create(self, validated_data):
        user = self.context['request'].user
        invitation = Invitation(inviter=user)
        invitation.save()
        EmailService().send_email("amirh.hamidian@gmail.com", "welcome to shooka",
                                  "hi\n you invited to " + user.company.name + "\nclick this link and complete your registration \n " "127.0.0.1:3000/register/agent/" + invitation.key)

        validated_data["username"] = validated_data["email"]
        validated_data["invitation"] = invitation
        validated_data["is_active"] = False
        validated_data["company"] = user.company

        return super(AgentSerializer, self).create(validated_data)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "phone_number",
            "company",
            "avatar",
            "teams",
            "email",
            "is_active",
        ]
        read_only_fields = ("id", "username", "company", "avatar", "is_active")


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
    client_sender = ClientSerializer(allow_null=True)
    agent_sender = AgentSerializer(allow_null=True)
    ticket_id = serializers.IntegerField(write_only=True)

    def create(self, validated_data):
        validated_data["agent_sender"] = self.context['request'].user
        ticket_id = validated_data.pop("ticket_id")
        message = super(MessageSerializer, self).create(validated_data)
        ticket = get_object_or_404(Ticket, pk=ticket_id)
        ticket.messages.add(message)
        return message

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
            "ticket_id",
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
        read_only_fields = ('id', 'client', 'title', 'creation_time', 'messages', 'company')


class TicketCreateSerializer(ModelSerializer):
    client = ClientSerializer()
    messages = MessageSerializer(many=True)
    followers = AgentSerializer(many=True)

    # def is_valid(self, raise_exception=False):
    # def create(self, validated_data):
    #     user = self.context['request'].user
    #     invitation = Invitation(inviter=user)
    #     invitation.save()
    #     EmailService().send_email("amirh.hamidian@gmail.com", "welcome to shooka",
    #                               "hi\n you invited to " + user.company.name + "\nclick this link and complete your registration \n " "127.0.0.1:3000/register/agent/" + invitation.key)
    #
    #     validated_data["username"] = validated_data["email"]
    #     validated_data["invitation"] = invitation
    #     validated_data["is_active"] = False
    #     validated_data["company"] = user.company
    #
    #     return super(TicketCreateSerializer, self).create(validated_data)

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
        read_only_fields = ('id', 'client', 'title', 'creation_time', 'messages', 'company')


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
            user.last_name = validated_data["last_name"]

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


class AgentSetPasswordSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    invitation_key = serializers.CharField(write_only=True)

    def create(self, validated_data):
        agent = get_object_or_404(User, invitation__key=validated_data["invitation_key"])
        agent.set_password(validated_data["password"])
        agent.is_active = True
        agent.save()
        return agent

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "password",
            "first_name",
            "last_name",
            "company",
            "invitation_key",
        ]
        read_only_fields = ('id', 'company')
