from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework import serializers
from servers.serializers import (
    ServerCreateSerializer,
    ServerSerializer,
    ServerMembershipCreateSerializer,
    ServerMembershipSerializer,
)
from servers.models import Server, ServerMembership

User = get_user_model()


class ServerCreateSerializerTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@example.com", password="Pass@123"
        )
        self.valid_data = {
            "name": "Server001",
            "description": "This is a dummy server",
            "icon": None,
            "visibility": "public",
        }

    def test_create_server(self):
        serializer = ServerCreateSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
        server = serializer.save(owner=self.user)
        self.assertEqual(server.name, "Server001")
        self.assertEqual(server.description, "This is a dummy server")
        self.assertEqual(server.visibility, "public")
        self.assertEqual(server.icon, None)
        self.assertEqual(server.owner, self.user)

    def test_missing_required_fields(self):
        required_fields = ["name"]

        for field in required_fields:
            with self.subTest(field=field):
                data = self.valid_data.copy()

                del data[field]

                serializer = ServerCreateSerializer(data=data)

                self.assertFalse(serializer.is_valid())
                self.assertIn(field, serializer.errors)

    def test_optional_fields_can_be_omitted(self):
        data = self.valid_data.copy()
        del data["visibility"]

        serializer = ServerCreateSerializer(data=data)

        self.assertTrue(serializer.is_valid())
        server = serializer.save(owner=self.user)
        self.assertEqual(
            server.visibility, "public"
        )  # visibility is created by default even if omitted from input

    def test_empty_optional_fields(self):
        data = self.valid_data.copy()
        data["description"] = ""

        serializer = ServerCreateSerializer(data=data)

        self.assertTrue(serializer.is_valid())
        server = serializer.save(owner=self.user)
        self.assertEqual(server.description, "")


class ServerSerializerTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@example.com", password="Pass@123", display_name="Test User"
        )
        self.user2 = User.objects.create_user(
            email="testuser2@example.com",
            password="Pass@123",
            display_name="Test User 2",
        )
        self.server = Server.objects.create(
            name="Test Server",
            description="Test description",
            visibility="public",
            owner=self.user,
        )

    def test_serializer_contains_expected_fields(self):
        serializer = ServerSerializer(instance=self.server)
        data = serializer.data

        expected_fields = [
            "id",
            "name",
            "description",
            "icon",
            "visibility",
            "owner",
            "member_count",
            "created_at",
            "updated_at",
        ]

        for field in expected_fields:
            with self.subTest(field=field):
                self.assertIn(field, data)

    def test_owner_field_is_nested_user_serializer(self):
        serializer = ServerSerializer(instance=self.server)
        data = serializer.data

        # Check that owner is a nested object, not just an ID
        self.assertIsInstance(data["owner"], dict)
        self.assertIn("id", data["owner"])
        self.assertIn("display_name", data["owner"])
        self.assertEqual(data["owner"]["display_name"], "Test User")

    def test_member_count_field(self):
        # Initially no members
        serializer = ServerSerializer(instance=self.server)
        data = serializer.data
        self.assertEqual(data["member_count"], 1)

        # Add members
        self.server.members.add(self.user2)

        # Refresh and check
        serializer = ServerSerializer(instance=self.server)
        data = serializer.data
        self.assertEqual(data["member_count"], 2)

    def test_read_only_fields_are_present(self):
        serializer = ServerSerializer(instance=self.server)
        data = serializer.data

        # These fields should be present in serialized data
        self.assertIsNotNone(data["id"])
        self.assertIsNotNone(data["created_at"])
        self.assertIsNotNone(data["updated_at"])
        self.assertIsNotNone(data["member_count"])
        self.assertIsNotNone(data["owner"])

    def test_serializer_with_all_fields_populated(self):

        serializer = ServerSerializer(instance=self.server)
        data = serializer.data
        new_serializer = ServerSerializer(data=data)
        self.assertTrue(new_serializer.is_valid())
        server = new_serializer.save(
            invite_code="ABC123", visibility="private", owner=self.user
        )
        self.assertEqual(server.name, "Test Server")
        self.assertEqual(server.description, "Test description")
        self.assertEqual(server.visibility, "private")
        self.assertEqual(server.invite_code, "ABC123")

    def test_serializer_with_empty_optional_fields(self):
        # Create server with minimal data
        minimal_server = Server.objects.create(name="Minimal Server", owner=self.user)

        serializer = ServerSerializer(instance=minimal_server)
        data = serializer.data

        self.assertEqual(data["name"], "Minimal Server")
        self.assertEqual(data["description"], "")
        self.assertEqual(data["visibility"], "public")  # Default value
        self.assertIsNone(data["icon"])
        self.assertEqual(data["member_count"], 1)

    def test_multiple_servers_serialization(self):
        # Create another server
        server2 = Server.objects.create(
            name="Server 2", description="Second server", owner=self.user2
        )

        servers = [self.server, server2]
        serializer = ServerSerializer(servers, many=True)
        data = serializer.data

        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["name"], "Test Server")
        self.assertEqual(data[1]["name"], "Server 2")
        self.assertEqual(data[0]["owner"]["display_name"], "Test User")
        self.assertEqual(data[1]["owner"]["display_name"], "Test User 2")


class ServerMembershipCreateSerializerTests(TestCase):

    def setUp(self):
        self.owner = User.objects.create_user(
            email="owner@example.com", password="Pass@123", display_name="Server Owner"
        )
        self.user = User.objects.create_user(
            email="member@example.com", password="Pass@123", display_name="Member User"
        )
        self.server = Server.objects.create(name="Test Server", owner=self.owner)

    def test_create_membership_with_valid_data(self):
        data = {"user": self.user.id, "role": "member"}

        serializer = ServerMembershipCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        membership = serializer.save(server=self.server)
        self.assertEqual(membership.user, self.user)
        self.assertEqual(membership.server, self.server)
        self.assertEqual(membership.role, "member")

    def test_create_membership_with_admin_role(self):
        data = {"user": self.user.id, "role": "admin"}

        serializer = ServerMembershipCreateSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        membership = serializer.save(server=self.server)
        self.assertEqual(membership.role, "admin")

    def test_missing_required_fields(self):
        required_fields = ["user"]

        for field in required_fields:
            with self.subTest(field=field):
                data = {"user": self.user.id}
                del data[field]

                serializer = ServerMembershipCreateSerializer(data=data)
                self.assertFalse(serializer.is_valid())
                self.assertIn(field, serializer.errors)

    def test_invalid_role_choice(self):
        data = {"user": self.user.id, "role": "invalid_role"}

        serializer = ServerMembershipCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("role", serializer.errors)

    def test_invalid_user_id(self):
        data = {"user": "invalid-uuid", "role": "member"}

        serializer = ServerMembershipCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("user", serializer.errors)

    def test_nonexistent_user_id(self):
        import uuid

        fake_uuid = uuid.uuid4()

        data = {"user": fake_uuid, "role": "member"}

        serializer = ServerMembershipCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("user", serializer.errors)


class ServerMembershipSerializerTests(TestCase):

    def setUp(self):
        self.owner = User.objects.create_user(
            email="owner@example.com", password="Pass@123", display_name="Server Owner"
        )
        self.member = User.objects.create_user(
            email="member@example.com", password="Pass@123", display_name="Member User"
        )
        self.server = Server.objects.create(
            name="Test Server", description="Test Description", owner=self.owner
        )
        self.membership = ServerMembership.objects.create(
            user=self.member, server=self.server, role="member"
        )

    def test_serializer_contains_expected_fields(self):
        serializer = ServerMembershipSerializer(instance=self.membership)
        data = serializer.data

        expected_fields = ["id", "user", "server", "role", "created_at", "updated_at"]

        for field in expected_fields:
            with self.subTest(field=field):
                self.assertIn(field, data)

    def test_user_field_is_nested_serializer(self):
        serializer = ServerMembershipSerializer(instance=self.membership)
        data = serializer.data

        # Check that user is a nested object
        self.assertIsInstance(data["user"], dict)
        self.assertIn("id", data["user"])
        self.assertIn("display_name", data["user"])
        self.assertEqual(data["user"]["display_name"], "Member User")

    def test_server_field_is_nested_serializer(self):
        serializer = ServerMembershipSerializer(instance=self.membership)
        data = serializer.data

        # Check that server is a nested object
        self.assertIsInstance(data["server"], dict)
        self.assertIn("id", data["server"])
        self.assertIn("name", data["server"])
        self.assertEqual(data["server"]["name"], "Test Server")

    def test_role_field_serialization(self):
        # Test different roles
        roles = ["admin", "moderator", "member"]

        for i, role in enumerate(roles):
            with self.subTest(role=role):
                user = User.objects.create_user(
                    email=f"user{i}@example.com",
                    password="Pass@123",
                    display_name=f"User {i}",
                )
                membership = ServerMembership.objects.create(
                    user=user, server=self.server, role=role
                )

                serializer = ServerMembershipSerializer(instance=membership)
                data = serializer.data
                self.assertEqual(data["role"], role)

    def test_timestamps_are_present(self):
        serializer = ServerMembershipSerializer(instance=self.membership)
        data = serializer.data

        self.assertIsNotNone(data["created_at"])
        self.assertIsNotNone(data["updated_at"])

    def test_multiple_memberships_serialization(self):
        # Create another membership
        user2 = User.objects.create_user(
            email="user2@example.com", password="Pass@123", display_name="User Two"
        )
        membership2 = ServerMembership.objects.create(
            user=user2, server=self.server, role="admin"
        )

        memberships = [self.membership, membership2]
        serializer = ServerMembershipSerializer(memberships, many=True)
        data = serializer.data

        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["role"], "member")
        self.assertEqual(data[1]["role"], "admin")
        self.assertEqual(data[0]["user"]["display_name"], "Member User")
        self.assertEqual(data[1]["user"]["display_name"], "User Two")
