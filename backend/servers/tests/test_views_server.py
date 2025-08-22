from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from servers.models import Server, ServerMembership
import json
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()


class ServerListViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create test users
        self.user1 = User.objects.create_user(
            email="user1@test.com", password="testpass123", display_name="User One"
        )
        self.user2 = User.objects.create_user(
            email="user2@test.com", password="testpass123", display_name="User Two"
        )
        self.user3 = User.objects.create_user(
            email="user3@test.com", password="testpass123", display_name="User Three"
        )

        # Create test servers
        self.public_server1 = Server.objects.create(
            name="Public Server 1",
            description="A public server",
            visibility="public",
            owner=self.user1,
        )

        self.private_server1 = Server.objects.create(
            name="Private Server 1",
            description="A private server",
            visibility="private",
            owner=self.user1,
        )

        self.gaming_server = Server.objects.create(
            name="Gaming Hub",
            description="For gamers",
            visibility="public",
            owner=self.user2,
        )

        # Create memberships
        ServerMembership.objects.create(
            user=self.user2, server=self.public_server1, role="admin"
        )
        ServerMembership.objects.create(
            user=self.user3, server=self.public_server1, role="member"
        )
        ServerMembership.objects.create(
            user=self.user1, server=self.gaming_server, role="moderator"
        )

    def test_get_servers_unauthenticated(self):
        """Test that unauthenticated users cannot access servers"""
        url = reverse("server-list")  # You'll need to add this URL pattern
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_all_servers_authenticated(self):
        """Test getting all servers when authenticated"""
        self.client.force_authenticate(user=self.user1)
        url = reverse("server-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Success")
        self.assertEqual(len(response.data["servers"]), 3)

    def test_filter_servers_by_owner(self):
        """Test filtering servers by member_type=owner"""
        self.client.force_authenticate(user=self.user1)
        url = reverse("server-list")
        response = self.client.get(url, {"member_type": "owner"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        servers = response.data["servers"]
        self.assertEqual(len(servers), 2)  # user1 owns 2 servers
        server_names = [s["name"] for s in servers]
        self.assertIn("Public Server 1", server_names)
        self.assertIn("Private Server 1", server_names)

    def test_filter_servers_by_admin_role(self):
        """Test filtering servers by member_type=admin"""
        self.client.force_authenticate(user=self.user2)
        url = reverse("server-list")
        response = self.client.get(url, {"member_type": "admin"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        servers = response.data["servers"]
        # user2 is admin of Public Server 1 and owner of Gaming Hub
        self.assertEqual(len(servers), 2)

    def test_filter_servers_by_member_role(self):
        """Test filtering servers by member_type=member"""
        self.client.force_authenticate(user=self.user3)
        url = reverse("server-list")
        response = self.client.get(url, {"member_type": "member"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        servers = response.data["servers"]
        self.assertEqual(len(servers), 1)
        self.assertEqual(servers[0]["name"], "Public Server 1")

    def test_filter_servers_by_visibility_public(self):
        """Test filtering servers by visibility=public"""
        self.client.force_authenticate(user=self.user1)
        url = reverse("server-list")
        response = self.client.get(url, {"visibility": "public"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        servers = response.data["servers"]
        self.assertEqual(len(servers), 2)
        for server in servers:
            self.assertEqual(server["visibility"], "public")

    def test_filter_servers_by_visibility_private(self):
        """Test filtering servers by visibility=private"""
        self.client.force_authenticate(user=self.user1)
        url = reverse("server-list")
        response = self.client.get(url, {"visibility": "private"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        servers = response.data["servers"]
        self.assertEqual(len(servers), 1)
        self.assertEqual(servers[0]["name"], "Private Server 1")

    def test_search_servers_by_name(self):
        """Test searching servers by name"""
        self.client.force_authenticate(user=self.user1)
        url = reverse("server-list")
        response = self.client.get(url, {"search": "gaming"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        servers = response.data["servers"]
        self.assertEqual(len(servers), 1)
        self.assertEqual(servers[0]["name"], "Gaming Hub")

    def test_search_servers_case_insensitive(self):
        """Test that search is case insensitive"""
        self.client.force_authenticate(user=self.user1)
        url = reverse("server-list")
        response = self.client.get(url, {"search": "GAMING"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        servers = response.data["servers"]
        self.assertEqual(len(servers), 1)
        self.assertEqual(servers[0]["name"], "Gaming Hub")

    def test_combined_filters(self):
        """Test combining multiple filters"""
        self.client.force_authenticate(user=self.user1)
        url = reverse("server-list")
        response = self.client.get(
            url, {"member_type": "owner", "visibility": "public"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        servers = response.data["servers"]
        self.assertEqual(len(servers), 1)
        self.assertEqual(servers[0]["name"], "Public Server 1")

    def test_create_server_success(self):
        """Test successful server creation"""
        self.client.force_authenticate(user=self.user1)
        url = reverse("server-list")

        data = {
            "name": "New Test Server",
            "description": "A new server for testing",
            "visibility": "public",
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["message"], "Server created successfully")
        self.assertEqual(response.data["server"]["name"], "New Test Server")

        # Verify server was created in database
        server = Server.objects.get(name="New Test Server")
        self.assertEqual(server.owner, self.user1)
        self.assertEqual(server.visibility, "public")

        # Verify owner membership was created
        membership = ServerMembership.objects.get(user=self.user1, server=server)
        self.assertEqual(membership.role, "owner")

    def test_create_server_with_icon(self):
        """Test creating server with icon upload"""
        self.client.force_authenticate(user=self.user1)
        url = reverse("server-list")

        # Create a test image file
        image = Image.new("RGB", (100, 100), color="red")
        image_file = BytesIO()
        image.save(image_file, format="PNG")
        image_file.seek(0)

        uploaded_file = SimpleUploadedFile(
            name="test_icon.png",
            content=image_file.getvalue(),
            content_type="image/png",
        )

        data = {
            "name": "Server with Icon",
            "description": "Testing icon upload",
            "visibility": "private",
            "icon": uploaded_file,
        }

        response = self.client.post(url, data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        server = Server.objects.get(name="Server with Icon")
        self.assertTrue(server.icon)

    def test_create_server_missing_required_field(self):
        """Test server creation with missing required field"""
        self.client.force_authenticate(user=self.user1)
        url = reverse("server-list")

        data = {"description": "Missing name field", "visibility": "public"}

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)

    def test_create_server_invalid_visibility(self):
        """Test server creation with invalid visibility choice"""
        self.client.force_authenticate(user=self.user1)
        url = reverse("server-list")

        data = {"name": "Test Server", "visibility": "invalid_choice"}

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("visibility", response.data)

    def test_create_server_unauthenticated(self):
        """Test that unauthenticated users cannot create servers"""
        url = reverse("server-list")
        data = {"name": "Test Server"}

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ServerDetailViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Create test users
        self.owner = User.objects.create_user(
            email="owner@test.com", password="testpass123", display_name="Owner User"
        )
        self.admin_user = User.objects.create_user(
            email="admin@test.com", password="testpass123", display_name="Admin User"
        )
        self.member_user = User.objects.create_user(
            email="member@test.com", password="testpass123", display_name="Member User"
        )
        self.outsider = User.objects.create_user(
            email="outsider@test.com",
            password="testpass123",
            display_name="Outsider User",
        )

        # Create test servers
        self.public_server = Server.objects.create(
            name="Public Test Server",
            description="A public server for testing",
            visibility="public",
            owner=self.owner,
        )

        self.private_server = Server.objects.create(
            name="Private Test Server",
            description="A private server for testing",
            visibility="private",
            owner=self.owner,
        )

        # Create memberships
        ServerMembership.objects.create(
            user=self.admin_user, server=self.public_server, role="admin"
        )
        ServerMembership.objects.create(
            user=self.member_user, server=self.public_server, role="member"
        )
        ServerMembership.objects.create(
            user=self.admin_user, server=self.private_server, role="admin"
        )

    def test_get_public_server_as_owner(self):
        """Test owner can access public server details"""
        self.client.force_authenticate(user=self.owner)
        url = reverse("server-detail", kwargs={"pk": self.public_server.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Success")
        self.assertEqual(response.data["server"]["name"], "Public Test Server")

    def test_get_public_server_as_member(self):
        """Test member can access public server details"""
        self.client.force_authenticate(user=self.member_user)
        url = reverse("server-detail", kwargs={"pk": self.public_server.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["server"]["name"], "Public Test Server")

    def test_get_public_server_as_outsider(self):
        """Test outsider can access public server details"""
        self.client.force_authenticate(user=self.outsider)
        url = reverse("server-detail", kwargs={"pk": self.public_server.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["server"]["name"], "Public Test Server")

    def test_get_private_server_as_owner(self):
        """Test owner can access private server details"""
        self.client.force_authenticate(user=self.owner)
        url = reverse("server-detail", kwargs={"pk": self.private_server.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["server"]["name"], "Private Test Server")

    def test_get_private_server_as_member(self):
        """Test member can access private server details"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("server-detail", kwargs={"pk": self.private_server.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["server"]["name"], "Private Test Server")

    def test_get_private_server_as_outsider_forbidden(self):
        """Test outsider cannot access private server details"""
        self.client.force_authenticate(user=self.outsider)
        url = reverse("server-detail", kwargs={"pk": self.private_server.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error"], "Permission Denied")

    def test_get_nonexistent_server(self):
        """Test getting details of nonexistent server"""
        self.client.force_authenticate(user=self.owner)
        url = reverse(
            "server-detail", kwargs={"pk": "00000000-0000-0000-0000-000000000000"}
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["message"], "Not found")

    def test_patch_server_as_owner(self):
        """Test owner can update server details"""
        self.client.force_authenticate(user=self.owner)
        url = reverse("server-detail", kwargs={"pk": self.public_server.pk})

        data = {"name": "Updated Server Name", "description": "Updated description"}

        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["message"], "Server details updated successfully"
        )
        self.assertEqual(response.data["server"]["name"], "Updated Server Name")

        # Verify database was updated
        self.public_server.refresh_from_db()
        self.assertEqual(self.public_server.name, "Updated Server Name")

    def test_patch_server_as_admin(self):
        """Test admin can update server details"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("server-detail", kwargs={"pk": self.public_server.pk})

        data = {"description": "Updated by admin"}

        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["server"]["description"], "Updated by admin")

    def test_patch_server_as_member_forbidden(self):
        """Test member cannot update server details"""
        self.client.force_authenticate(user=self.member_user)
        url = reverse("server-detail", kwargs={"pk": self.public_server.pk})

        data = {"name": "Unauthorized Update"}

        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("Permission denied", response.data["error"])

    def test_patch_server_as_outsider_forbidden(self):
        """Test outsider cannot update server details"""
        self.client.force_authenticate(user=self.outsider)
        url = reverse("server-detail", kwargs={"pk": self.public_server.pk})

        data = {"name": "Unauthorized Update"}

        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_patch_nonexistent_server(self):
        """Test updating nonexistent server"""
        self.client.force_authenticate(user=self.owner)
        url = reverse(
            "server-detail", kwargs={"pk": "00000000-0000-0000-0000-000000000000"}
        )

        data = {"name": "Does not exist"}

        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["message"], "Server does not exist.")

    def test_delete_server_as_owner(self):
        """Test owner can delete server"""
        self.client.force_authenticate(user=self.owner)
        url = reverse("server-detail", kwargs={"pk": self.public_server.pk})

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify server was deleted
        with self.assertRaises(Server.DoesNotExist):
            Server.objects.get(pk=self.public_server.pk)

    def test_delete_server_as_admin_forbidden(self):
        """Test admin cannot delete server (owner only)"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("server-detail", kwargs={"pk": self.public_server.pk})

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("Permission denied", response.data["error"])

    def test_delete_server_as_outsider_forbidden(self):
        """Test outsider cannot delete server"""
        self.client.force_authenticate(user=self.outsider)
        url = reverse("server-detail", kwargs={"pk": self.public_server.pk})

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_nonexistent_server(self):
        """Test deleting nonexistent server"""
        self.client.force_authenticate(user=self.owner)
        url = reverse(
            "server-detail", kwargs={"pk": "00000000-0000-0000-0000-000000000000"}
        )

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["message"], "Server does not exist.")

    def test_unauthenticated_access_forbidden(self):
        """Test unauthenticated users cannot access server details"""
        url = reverse("server-detail", kwargs={"pk": self.public_server.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ServerViewsIntegrationTests(TestCase):
    """Integration tests for server views working together"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@test.com", password="testpass123", display_name="Test User"
        )
        self.client.force_authenticate(user=self.user)

    def test_create_and_retrieve_server_flow(self):
        """Test creating a server and then retrieving it"""
        # Create server
        create_url = reverse("server-list")
        create_data = {
            "name": "Integration Test Server",
            "description": "Created in integration test",
            "visibility": "public",
        }

        create_response = self.client.post(create_url, create_data)
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        server_id = create_response.data["server"]["id"]

        # Retrieve server details
        detail_url = reverse("server-detail", kwargs={"pk": server_id})
        detail_response = self.client.get(detail_url)

        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            detail_response.data["server"]["name"], "Integration Test Server"
        )

    def test_create_update_delete_server_flow(self):
        """Test complete CRUD flow for server"""
        # Create
        create_url = reverse("server-list")
        create_data = {"name": "CRUD Test Server", "visibility": "private"}
        create_response = self.client.post(create_url, create_data)
        server_id = create_response.data["server"]["id"]

        # Update
        detail_url = reverse("server-detail", kwargs={"pk": server_id})
        update_data = {"name": "Updated CRUD Server"}
        update_response = self.client.patch(detail_url, update_data, format="json")
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.data["server"]["name"], "Updated CRUD Server")

        # Delete
        delete_response = self.client.delete(detail_url)
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify deleted
        get_response = self.client.get(detail_url)
        self.assertEqual(get_response.status_code, status.HTTP_404_NOT_FOUND)
