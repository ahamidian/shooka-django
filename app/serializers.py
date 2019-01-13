from django.db.models import When
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer, Serializer
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from app.models import Ticket, User, Team, Message, Company, Invitation, Client, Criteria, SingleCriteria, \
    CriteriaClause
from app.servises import EmailService


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):

    def validate(self, attrs):
        data = super(MyTokenObtainPairSerializer, self).validate(attrs)
        serializer = AgentSerializer(instance=self.user)
        data['user'] = serializer.data
        return data


class AgentSerializer(ModelSerializer):
    avatar = serializers.SerializerMethodField()

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

    def get_avatar(self, obj):
        if obj.avatar:
            return "http://127.0.0.1:8000" + obj.avatar.url
        return None

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
            "signature",
        ]
        read_only_fields = ("id", "username", "company", "avatar", "is_active")


class ClientSerializer(ModelSerializer):
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = [
            "id",
            "name",
            "email",
            "avatar",
        ]

    def get_avatar(self, obj):
        if obj.avatar:
            return "http://127.0.0.1:8000" + obj.avatar.url
        return None


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

    def create(self, validated_data):
        validated_data["agent_sender"] = self.context['request'].user
        message = super(MessageSerializer, self).create(validated_data)
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
            "ticket",
        ]


class TicketListSerializer(ModelSerializer):
    client = ClientSerializer()

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
    messages = serializers.SerializerMethodField()
    followers = AgentSerializer(many=True)

    def get_messages(self, instance):
        messages = instance.message_set.all().order_by('creation_time')
        return MessageSerializer(messages, many=True).data

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
    messages = serializers.SerializerMethodField()
    followers = AgentSerializer(many=True)

    def get_messages(self, instance):
        messages = instance.message_set.all().order_by('creation_time')
        return MessageSerializer(messages, many=True).data

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


class TicketSplitSerializer(Serializer):
    messages = serializers.ListField()
    ticket_title = serializers.CharField()
    ticket_id = serializers.IntegerField()

    def save(self, **kwargs):
        old_ticket = Ticket.objects.get(pk=self.validated_data["ticket_id"])
        new_ticket = Ticket.objects.create(
            client=old_ticket.client,
            title=self.validated_data["ticket_title"],
            creation_time=old_ticket.creation_time,
            status=old_ticket.status,
            priority=old_ticket.priority,
            # tags=old_ticket.tags,
            assigned_to=old_ticket.assigned_to,
            assigned_team=old_ticket.assigned_team,
            # followers=old_ticket.followers,
            company=old_ticket.company,
        )

        for message_id in self.validated_data["messages"]:
            message = Message.objects.get(pk=message_id)
            message.ticket = new_ticket
            message.save()

        return old_ticket


class TicketMergeSerializer(Serializer):
    origin_ticket = serializers.IntegerField()
    destination_ticket = serializers.IntegerField()

    def save(self, **kwargs):
        origin_ticket = Ticket.objects.get(pk=self.validated_data["origin_ticket"])
        destination_ticket = Ticket.objects.get(pk=self.validated_data["destination_ticket"])

        origin_ticket.message_set.update(ticket=destination_ticket)
        origin_ticket.delete()
        # for message in origin_ticket:
        #     message.ticket = destination_ticket
        #     message.save()

        return destination_ticket

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


class SingleCriteriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = SingleCriteria
        fields = [
            "id",
            "field",
            "value",
            "value_type",
            "operation",
        ]

        read_only_fields = ['id']


class CriteriaClauseSerializer(serializers.ModelSerializer):
    singles = SingleCriteriaSerializer(many=True)

    class Meta:
        model = CriteriaClause
        fields = [
            "id",
            "singles",
        ]

        read_only_fields = ['id']


class CriteriaSerializer(serializers.ModelSerializer):
    clauses = CriteriaClauseSerializer(many=True)

    def create(self, validated_data):
        clauses = validated_data.pop("clauses")
        criteria = super(CriteriaSerializer, self).create(validated_data)
        for clause in clauses:
            clause_serializer = CriteriaClauseSerializer(data=clause)
            clause_serializer.is_valid()
            criteria_clause = CriteriaClause.objects.create(criteria=criteria)
            singles = clause_serializer.validated_data["singles"]
            for single in singles:
                single_serializer = SingleCriteriaSerializer(data=single)
                single_serializer.is_valid()
                single_serializer.validated_data["criteria_clause"] = criteria_clause
                single_criteria = single_serializer.save()
        return criteria

    class Meta:
        model = Criteria
        fields = [
            "id",
            "name",
            "clauses",
        ]
        read_only_fields = ['id']
