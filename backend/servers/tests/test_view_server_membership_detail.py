from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from servers.models import Server, ServerMembership

User = get_user_model()


class ServerMembershipDetailViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create test users
        self.owner = User.objects.create_user(
            email="owner@test.com", password="testpass123", display_name="Server Owner"
        )
        self.admin_user = User.objects.create_user(
            email="admin@test.com", password="testpass123", display_name="Admin User"
        )
        self.member_user = User.objects.create_user(
            email="member@test.com", password="testpass123", display_name="Member User"
        )
        self.other_member = User.objects.create_user(
            email="other@test.com", password="testpass123", display_name="Other Member"
        )
        self.outsider = User.objects.create_user(
            email="outsider@test.com",
            password="testpass123",
            display_name="Outsider User",
        )

        # Create test server
        self.server = Server.objects.create(
            name="Test Server",
            description="A test server",
            visibility="public",
            owner=self.owner,
        )

        # Create memberships (owner membership auto-created)
        self.admin_membership = ServerMembership.objects.create(
            user=self.admin_user, server=self.server, role="admin"
        )
        self.member_membership = ServerMembership.objects.create(
            user=self.member_user, server=self.server, role="member"
        )
        self.other_membership = ServerMembership.objects.create(
            user=self.other_member, server=self.server, role="member"
        )

    def get_url(self, user_id):
        """Helper to get URL for membership detail"""
        return reverse(
            "server-membership-detail",
            kwargs={"server_id": self.server.pk, "user_id": user_id},
        )

    # =====================================
    # GET METHOD TESTS
    # =====================================

    def test_get_membership_unauthenticated(self):
        """Test that unauthenticated users cannot access membership details"""
        url = self.get_url(self.member_user.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_own_membership_success(self):
        """Test user can view their own membership"""
        self.client.force_authenticate(user=self.member_user)
        url = self.get_url(self.member_user.pk)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Success")

        membership_data = response.data["membership"]
        self.assertEqual(membership_data["role"], "member")
        self.assertEqual(membership_data["user"]["id"], str(self.member_user.id))

    def test_get_membership_as_server_owner(self):
        """Test server owner can view any membership"""
        self.client.force_authenticate(user=self.owner)
        url = self.get_url(self.member_user.pk)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["membership"]["role"], "member")

    def test_get_membership_as_server_admin(self):
        """Test server admin can view any membership"""
        self.client.force_authenticate(user=self.admin_user)
        url = self.get_url(self.member_user.pk)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_membership_as_other_member_forbidden(self):
        """Test member cannot view other member's membership details"""
        self.client.force_authenticate(user=self.member_user)
        url = self.get_url(self.other_member.pk)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error"], "Permission denied.")

    def test_get_nonexistent_membership(self):
        """Test getting nonexistent membership returns 404"""
        self.client.force_authenticate(user=self.owner)
        url = self.get_url(self.outsider.pk)  # Outsider is not a member
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "Membership does not exist.")

    # =====================================
    # PATCH METHOD TESTS
    # =====================================

    def test_patch_member_role_as_owner_success(self):
        """Test server owner can update member roles"""
        self.client.force_authenticate(user=self.owner)
        url = self.get_url(self.member_user.pk)

        data = {"role": "admin"}
        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Member role updated successfully.")
        self.assertEqual(response.data["membership"]["role"], "admin")

        # Verify database was updated
        self.member_membership.refresh_from_db()
        self.assertEqual(self.member_membership.role, "admin")

    def test_patch_member_role_as_admin_success(self):
        """Test server admin can update member roles"""
        self.client.force_authenticate(user=self.admin_user)
        url = self.get_url(self.member_user.pk)

        data = {"role": "moderator"}
        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["membership"]["role"], "moderator")

    def test_patch_owner_role_forbidden(self):
        """Test that owner's role cannot be changed"""
        self.client.force_authenticate(user=self.owner)
        url = self.get_url(self.owner.pk)

        data = {"role": "admin"}
        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["error"],
            "Cannot modify the owner's role. Transfer ownership first.",
        )

    def test_patch_self_role_forbidden(self):
        """Test that users cannot change their own role"""
        self.client.force_authenticate(user=self.member_user)
        url = self.get_url(self.member_user.pk)

        data = {"role": "admin"}
        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["error"],
            "You cannot change your own role. Ask an admin or owner.",
        )

    def test_patch_member_cannot_update_others(self):
        """Test that regular members cannot update other memberships"""
        self.client.force_authenticate(user=self.member_user)
        url = self.get_url(self.other_member.pk)

        data = {"role": "admin"}
        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("Permission denied", response.data["error"])

    def test_patch_invalid_fields_forbidden(self):
        """Test that only role field can be updated"""
        self.client.force_authenticate(user=self.owner)
        url = self.get_url(self.member_user.pk)

        data = {"user": str(self.other_member.id), "role": "admin"}
        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Cannot update fields: user", response.data["error"])

    def test_patch_nonexistent_membership(self):
        """Test updating nonexistent membership returns 404"""
        self.client.force_authenticate(user=self.owner)
        url = self.get_url(self.outsider.pk)

        data = {"role": "admin"}
        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # =====================================
    # DELETE METHOD TESTS
    # =====================================

    def test_delete_own_membership_success(self):
        """Test user can leave server (delete own membership)"""
        self.client.force_authenticate(user=self.member_user)
        url = self.get_url(self.member_user.pk)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], f"You have left {self.server.name}.")

        # Verify membership was deleted
        with self.assertRaises(ServerMembership.DoesNotExist):
            ServerMembership.objects.get(pk=self.member_membership.pk)

    def test_delete_member_as_owner_success(self):
        """Test server owner can remove members"""
        self.client.force_authenticate(user=self.owner)
        url = self.get_url(self.member_user.pk)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["message"],
            f"{self.member_user.display_name} has been removed from {self.server.name}.",
        )

        # Verify membership was deleted
        with self.assertRaises(ServerMembership.DoesNotExist):
            ServerMembership.objects.get(pk=self.member_membership.pk)

    def test_delete_owner_membership_forbidden(self):
        """Test that server owner cannot leave their own server"""
        self.client.force_authenticate(user=self.owner)
        url = self.get_url(self.owner.pk)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["error"],
            "Server owners cannot leave their own server. Transfer ownership or delete the server.",
        )

    def test_delete_admin_cannot_remove_owner(self):
        """Test that admin cannot remove server owner"""
        self.client.force_authenticate(user=self.admin_user)
        url = self.get_url(self.owner.pk)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            response.data["error"], "Admins cannot remove the server owner."
        )

    def test_delete_member_cannot_remove_others(self):
        """Test that regular members cannot remove other members"""
        self.client.force_authenticate(user=self.member_user)
        url = self.get_url(self.other_member.pk)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_nonexistent_membership(self):
        """Test deleting nonexistent membership returns 404"""
        self.client.force_authenticate(user=self.owner)
        url = self.get_url(self.outsider.pk)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # =====================================
    # PERMISSION HIERARCHY TESTS
    # =====================================

    def test_permission_hierarchy_consistency(self):
        """Test that permission hierarchy is consistent across methods"""
        test_cases = [
            (self.owner, True, "owner"),
            (self.admin_user, True, "admin"),
            (self.member_user, False, "other_member"),
            (self.outsider, False, "outsider"),
        ]

        for user, should_have_access, role in test_cases:
            with self.subTest(user=role):
                self.client.force_authenticate(user=user)
                url = self.get_url(self.other_member.pk)

                # Test GET
                get_response = self.client.get(url)
                if should_have_access:
                    self.assertEqual(get_response.status_code, status.HTTP_200_OK)
                else:
                    self.assertEqual(
                        get_response.status_code, status.HTTP_403_FORBIDDEN
                    )

    # =====================================
    # INTEGRATION TESTS
    # =====================================

    def test_role_update_chain(self):
        """Test updating a member through different role levels"""
        self.client.force_authenticate(user=self.owner)
        url = self.get_url(self.member_user.pk)

        # member -> moderator
        response1 = self.client.patch(url, {"role": "moderator"}, format="json")
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response1.data["membership"]["role"], "moderator")

        # moderator -> admin
        response2 = self.client.patch(url, {"role": "admin"}, format="json")
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.data["membership"]["role"], "admin")

        # admin -> member (demotion)
        response3 = self.client.patch(url, {"role": "member"}, format="json")
        self.assertEqual(response3.status_code, status.HTTP_200_OK)
        self.assertEqual(response3.data["membership"]["role"], "member")

    def test_membership_lifecycle_flow(self):
        """Test complete membership lifecycle: view, update, delete"""
        self.client.force_authenticate(user=self.owner)
        url = self.get_url(self.member_user.pk)

        # View membership
        get_response = self.client.get(url)
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_response.data["membership"]["role"], "member")

        # Update role
        patch_response = self.client.patch(url, {"role": "moderator"}, format="json")
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_response.data["membership"]["role"], "moderator")

        # Delete membership
        delete_response = self.client.delete(url)
        self.assertEqual(delete_response.status_code, status.HTTP_200_OK)

        # Verify it's gone
        final_get_response = self.client.get(url)
        self.assertEqual(final_get_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_url_pattern_with_user_id(self):
        """Test that URL pattern correctly uses user_id"""
        # Test URL generation
        url = reverse(
            "server-membership-detail",
            kwargs={"server_id": self.server.pk, "user_id": self.member_user.pk},
        )

        # URL should contain both server and user IDs
        self.assertIn(str(self.server.pk), url)
        self.assertIn(str(self.member_user.pk), url)

        # Test actual request
        self.client.force_authenticate(user=self.member_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cross_server_membership_isolation(self):
        """Test that memberships are properly isolated between servers"""
        # Create another server
        other_server = Server.objects.create(name="Other Server", owner=self.admin_user)
        ServerMembership.objects.create(
            user=self.member_user, server=other_server, role="admin"
        )

        # Request membership from first server
        self.client.force_authenticate(user=self.owner)
        url = self.get_url(self.member_user.pk)
        response = self.client.get(url)

        # Should get membership from correct server
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["membership"]["server"]["id"], str(self.server.id)
        )
        self.assertEqual(response.data["membership"]["role"], "member")
