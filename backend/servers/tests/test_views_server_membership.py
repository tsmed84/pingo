from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from servers.models import Server, ServerMembership
import json

User = get_user_model()


class ServerMembershipListViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create test users
        self.owner = User.objects.create_user(
            email="owner@test.com", password="testpass123", display_name="Server Owner"
        )
        self.member1 = User.objects.create_user(
            email="member1@test.com", password="testpass123", display_name="Member One"
        )
        self.member2 = User.objects.create_user(
            email="member2@test.com", password="testpass123", display_name="Member Two"
        )
        self.admin_user = User.objects.create_user(
            email="admin@test.com", password="testpass123", display_name="Admin User"
        )
        self.outsider = User.objects.create_user(
            email="outsider@test.com",
            password="testpass123",
            display_name="Outsider User",
        )

        # Create test servers
        self.public_server = Server.objects.create(
            name="Public Gaming Server",
            description="A public server for gaming",
            visibility="public",
            owner=self.owner,
        )

        self.private_server = Server.objects.create(
            name="Private Team Server",
            description="A private server for team",
            visibility="private",
            invite_code="SECRET123",
            owner=self.owner,
        )

        self.empty_server = Server.objects.create(
            name="Empty Server",
            description="Server with only owner",
            visibility="public",
            owner=self.member1,
        )

        # Create memberships
        # Note: Owner memberships are created automatically by model save()
        ServerMembership.objects.create(
            user=self.member1, server=self.public_server, role="member"
        )
        ServerMembership.objects.create(
            user=self.member2, server=self.public_server, role="member"
        )
        ServerMembership.objects.create(
            user=self.admin_user, server=self.public_server, role="admin"
        )

        # Private server memberships
        ServerMembership.objects.create(
            user=self.admin_user, server=self.private_server, role="admin"
        )

    # =====================================
    # GET METHOD TESTS
    # =====================================

    def test_get_memberships_unauthenticated(self):
        """Test that unauthenticated users cannot access server memberships"""
        url = reverse("server-memberships", kwargs={"server_id": self.public_server.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_memberships_as_owner(self):
        """Test owner can see all server memberships"""
        self.client.force_authenticate(user=self.owner)
        url = reverse("server-memberships", kwargs={"server_id": self.public_server.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Success")

        memberships = response.data["memberships"]
        self.assertEqual(len(memberships), 4)

        # Check that response includes nested user data
        membership_names = [m["user"]["display_name"] for m in memberships]
        self.assertIn("Server Owner", membership_names)
        self.assertIn("Member One", membership_names)
        self.assertIn("Admin User", membership_names)

    def test_get_memberships_as_member(self):
        """Test member can see server memberships"""
        self.client.force_authenticate(user=self.member1)
        url = reverse("server-memberships", kwargs={"server_id": self.public_server.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        memberships = response.data["memberships"]
        self.assertEqual(len(memberships), 4)

    def test_get_memberships_as_admin(self):
        """Test admin can see server memberships"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("server-memberships", kwargs={"server_id": self.public_server.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        memberships = response.data["memberships"]
        self.assertEqual(len(memberships), 4)

    def test_get_memberships_as_outsider_public_server(self):
        """Test outsider cannot see public server memberships"""
        self.client.force_authenticate(user=self.outsider)
        url = reverse("server-memberships", kwargs={"server_id": self.public_server.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["error"],
            "Permission denied. You are not a member of this server.",
        )

    def test_get_memberships_as_outsider_private_server(self):
        """Test outsider cannot see private server memberships"""
        self.client.force_authenticate(user=self.outsider)
        url = reverse(
            "server-memberships", kwargs={"server_id": self.private_server.pk}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["error"],
            "Permission denied. You are not a member of this server.",
        )

    def test_get_memberships_nonexistent_server(self):
        """Test getting memberships of nonexistent server"""
        self.client.force_authenticate(user=self.owner)
        url = reverse(
            "server-memberships",
            kwargs={"server_id": "00000000-0000-0000-0000-000000000000"},
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "Server does not exist.")

    def test_get_memberships_with_role_filter(self):
        """Test filtering memberships by role using query parameters"""
        self.client.force_authenticate(user=self.owner)
        url = reverse("server-memberships", kwargs={"server_id": self.public_server.pk})
        response = self.client.get(url, {"role": "admin"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        memberships = response.data["memberships"]

        # Should only return admin members
        admin_memberships = [m for m in memberships if m["role"] == "admin"]
        self.assertEqual(len(admin_memberships), 1)
        self.assertEqual(admin_memberships[0]["user"]["display_name"], "Admin User")

    def test_get_memberships_with_search_filter(self):
        """Test searching memberships by user display name"""
        self.client.force_authenticate(user=self.owner)
        url = reverse("server-memberships", kwargs={"server_id": self.public_server.pk})
        response = self.client.get(url, {"search": "member"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        memberships = response.data["memberships"]

        # Should return users with "member" in their display name
        member_names = [m["user"]["display_name"] for m in memberships]
        self.assertTrue(any("Member" in name for name in member_names))

    def test_get_memberships_response_structure(self):
        """Test that membership response has correct structure"""
        self.client.force_authenticate(user=self.owner)
        url = reverse("server-memberships", kwargs={"server_id": self.public_server.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response structure
        self.assertIn("message", response.data)
        self.assertIn("memberships", response.data)

        # Check membership structure
        membership = response.data["memberships"][0]
        required_fields = ["id", "user", "server", "role", "created_at", "updated_at"]
        for field in required_fields:
            self.assertIn(field, membership)

        # Check nested user structure
        user = membership["user"]
        self.assertIn("id", user)
        self.assertIn("display_name", user)

        # Check nested server structure
        server = membership["server"]
        self.assertIn("id", server)
        self.assertIn("name", server)

    # =====================================
    # POST METHOD TESTS
    # =====================================

    def test_join_server_unauthenticated(self):
        """Test that unauthenticated users cannot join servers"""
        url = reverse("server-memberships", kwargs={"server_id": self.public_server.pk})
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_join_public_server_success(self):
        """Test successfully joining a public server"""
        self.client.force_authenticate(user=self.outsider)
        url = reverse("server-memberships", kwargs={"server_id": self.public_server.pk})
        response = self.client.post(url, {})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.data["message"],
            f"Congratulations! You have joined {self.public_server.name}.",
        )

        # Verify membership was created
        membership = ServerMembership.objects.get(
            user=self.outsider, server=self.public_server
        )
        self.assertEqual(membership.role, "member")  # Default role

        # Check response structure
        self.assertIn("membership", response.data)
        membership_data = response.data["membership"]
        self.assertEqual(membership_data["role"], "member")
        self.assertEqual(membership_data["user"]["id"], str(self.outsider.id))

    def test_join_private_server_with_valid_invite_code(self):
        """Test joining private server with valid invitation code"""
        self.client.force_authenticate(user=self.outsider)
        url = reverse(
            "server-memberships", kwargs={"server_id": self.private_server.pk}
        )

        data = {"invite_code": "SECRET123"}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify membership was created
        membership = ServerMembership.objects.get(
            user=self.outsider, server=self.private_server
        )
        self.assertEqual(membership.role, "member")

    def test_join_private_server_with_invalid_invite_code(self):
        """Test joining private server with invalid invitation code"""
        self.client.force_authenticate(user=self.outsider)
        url = reverse(
            "server-memberships", kwargs={"server_id": self.private_server.pk}
        )

        data = {"invite_code": "WRONG123"}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["error"],
            "This is a private server. You need a valid invitation code to join.",
        )

        # Verify membership was NOT created
        self.assertFalse(
            ServerMembership.objects.filter(
                user=self.outsider, server=self.private_server
            ).exists()
        )

    def test_join_private_server_without_invite_code(self):
        """Test joining private server without invitation code"""
        self.client.force_authenticate(user=self.outsider)
        url = reverse(
            "server-memberships", kwargs={"server_id": self.private_server.pk}
        )

        response = self.client.post(url, {})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["error"],
            "This is a private server. You need a valid invitation code to join.",
        )

    def test_owner_cannot_join_own_server(self):
        """Test that server owner cannot join their own server"""
        self.client.force_authenticate(user=self.owner)
        url = reverse("server-memberships", kwargs={"server_id": self.public_server.pk})
        response = self.client.post(url, {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["error"],
            "You are the owner of this server and already a member.",
        )

    def test_existing_member_cannot_join_again(self):
        """Test that existing member cannot join the same server again"""
        self.client.force_authenticate(user=self.member1)
        url = reverse("server-memberships", kwargs={"server_id": self.public_server.pk})
        response = self.client.post(url, {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["error"], "You are already a member of this server."
        )

    def test_join_nonexistent_server(self):
        """Test joining nonexistent server"""
        self.client.force_authenticate(user=self.outsider)
        url = reverse(
            "server-memberships",
            kwargs={"server_id": "00000000-0000-0000-0000-000000000000"},
        )
        response = self.client.post(url, {})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "Server does not exist.")

    def test_join_server_membership_count_increases(self):
        """Test that server membership count increases after joining"""
        # Get initial member count
        initial_count = ServerMembership.objects.filter(
            server=self.empty_server
        ).count()

        self.client.force_authenticate(user=self.outsider)
        url = reverse("server-memberships", kwargs={"server_id": self.empty_server.pk})
        response = self.client.post(url, {})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify count increased
        final_count = ServerMembership.objects.filter(server=self.empty_server).count()
        self.assertEqual(final_count, initial_count + 1)

    def test_join_server_creates_correct_membership_data(self):
        """Test that joining creates membership with correct data"""
        self.client.force_authenticate(user=self.outsider)
        url = reverse("server-memberships", kwargs={"server_id": self.public_server.pk})
        response = self.client.post(url, {})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify database record
        membership = ServerMembership.objects.get(
            user=self.outsider, server=self.public_server
        )
        self.assertEqual(membership.user, self.outsider)
        self.assertEqual(membership.server, self.public_server)
        self.assertEqual(membership.role, "member")  # Default role from model
        self.assertIsNotNone(membership.created_at)
        self.assertIsNotNone(membership.updated_at)

    def test_join_server_serializer_validation_error(self):
        """Test handling of serializer validation errors"""
        # This test would require creating invalid data that passes initial validation
        # but fails at serializer level. For now, it's a placeholder for edge cases
        pass

    # =====================================
    # INTEGRATION TESTS
    # =====================================

    def test_join_then_view_memberships_flow(self):
        """Test complete flow: join server then view memberships"""
        self.client.force_authenticate(user=self.outsider)

        # Join server
        join_url = reverse(
            "server-memberships", kwargs={"server_id": self.public_server.pk}
        )
        join_response = self.client.post(join_url, {})
        self.assertEqual(join_response.status_code, status.HTTP_201_CREATED)

        # Now view memberships (should work since user is now a member)
        view_url = reverse(
            "server-memberships", kwargs={"server_id": self.public_server.pk}
        )
        view_response = self.client.get(view_url)
        self.assertEqual(view_response.status_code, status.HTTP_200_OK)

        # Should see one more membership (including the new one)
        memberships = view_response.data["memberships"]
        self.assertEqual(len(memberships), 5)

    def test_multiple_users_joining_same_server(self):
        """Test multiple users joining the same server"""
        users = [self.outsider]

        # Create additional test user
        extra_user = User.objects.create_user(
            email="extra@test.com", password="testpass123", display_name="Extra User"
        )
        users.append(extra_user)

        url = reverse("server-memberships", kwargs={"server_id": self.empty_server.pk})

        for user in users:
            self.client.force_authenticate(user=user)
            response = self.client.post(url, {})
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify all memberships created
        final_count = ServerMembership.objects.filter(server=self.empty_server).count()
        self.assertEqual(final_count, 3)  # owner + 2 new members

    def test_join_server_response_matches_get_format(self):
        """Test that POST response format matches GET format for consistency"""
        self.client.force_authenticate(user=self.outsider)

        # Join server
        join_url = reverse(
            "server-memberships", kwargs={"server_id": self.public_server.pk}
        )
        join_response = self.client.post(join_url, {})
        join_membership = join_response.data["membership"]

        # Get memberships
        get_url = reverse(
            "server-memberships", kwargs={"server_id": self.public_server.pk}
        )
        get_response = self.client.get(get_url)
        get_memberships = get_response.data["memberships"]

        # Find the newly created membership
        new_membership = next(
            m for m in get_memberships if m["user"]["id"] == str(self.outsider.id)
        )

        # Compare structures (excluding dynamic fields like timestamps)
        self.assertEqual(join_membership["user"]["id"], new_membership["user"]["id"])
        self.assertEqual(
            join_membership["server"]["id"], new_membership["server"]["id"]
        )
        self.assertEqual(join_membership["role"], new_membership["role"])
