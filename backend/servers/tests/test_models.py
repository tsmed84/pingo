from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
import uuid
from servers.models import Server, ServerMembership

User = get_user_model()


class ServerTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123", display_name="Test User"
        )
        self.server = Server.objects.create(
            name="Server001",
            description="This is a server description",
            owner=self.user,
        )

    def test_create_server(self):
        server_count = Server.objects.count()
        self.assertEqual(server_count, 1)
        Server.objects.create(
            name="Server002",
            description="Just another server description",
            owner=self.user,
        )
        updated_server_count = Server.objects.count()
        self.assertEqual(updated_server_count, 2)

    def test_server_str_method(self):
        self.assertEqual(str(self.server), "Server001")

    def test_member_count_property(self):
        number_of_members = self.server.get_member_count
        self.assertEqual(number_of_members, 1)

    def test_visibility_choices(self):
        self.assertEqual(self.server.visibility, "public")


class ServerMembershipModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123", display_name="Test User"
        )
        self.user2 = User.objects.create_user(
            email="test2@example.com",
            password="testpass456",
            display_name="Test User 2",
        )
        self.server = Server.objects.create(
            name="Server001",
            description="This is a server description",
            owner=self.user,
        )

    def test_membership_creation(self):
        membership = ServerMembership.objects.create(
            user=self.user2, server=self.server, role="member"
        )
        self.assertEqual(ServerMembership.objects.count(), 2)
        self.assertEqual(membership.user, self.user2)
        self.assertEqual(membership.server, self.server)
        self.assertEqual(membership.role, "member")

    def test_unique_together_constraint(self):
        ServerMembership.objects.create(
            user=self.user2, server=self.server, role="member"
        )
        # Try to create duplicate membership
        with self.assertRaises(IntegrityError):
            ServerMembership.objects.create(
                user=self.user2, server=self.server, role="admin"
            )

    def test_membership_str_method(self):
        membership = ServerMembership.objects.create(
            user=self.user2, server=self.server, role="member"
        )
        expected_str = f"{self.user2.display_name} - {self.server.name}"
        self.assertEqual(str(membership), expected_str)

    def test_role_choices(self):
        membership = ServerMembership.objects.create(
            user=self.user2, server=self.server, role="admin"
        )
        self.assertEqual(membership.role, "admin")

        # Test default role
        user3 = User.objects.create_user(
            email="testuser3@example.com", password="Pass@123"
        )
        membership2 = ServerMembership.objects.create(user=user3, server=self.server)
        self.assertEqual(membership2.role, "member")
