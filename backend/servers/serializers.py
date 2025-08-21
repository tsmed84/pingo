from rest_framework import serializers
from .models import Server, ServerMembership
from accounts.serializers import UserProfileSerializer


class ServerCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Server
        fields = ["name", "description", "icon", "visibility"]


class ServerSerializer(serializers.ModelSerializer):
    member_count = serializers.ReadOnlyField(source="get_member_count")
    owner = UserProfileSerializer(read_only=True)

    class Meta:
        model = Server
        fields = [
            "id",
            "name",
            "description",
            "icon",
            "member_count",
            "visibility",
            "owner",
            "created_at",
            "updated_at",
        ]


class ServerMembershipCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServerMembership
        fields = ["user", "role"]


class ServerMembershipSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    server = ServerSerializer(read_only=True)

    class Meta:
        model = ServerMembership
        fields = ["id", "user", "server", "role", "created_at", "updated_at"]
