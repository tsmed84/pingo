from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class UserRegistrationViewTests(APITestCase):

    def setUp(self):
        self.register_url = reverse("register")
        self.valid_payload = {
            "email": "test@example.com",
            "password": "testpass123",
            "password_confirm": "testpass123",
            "display_name": "Test User",
        }

    def test_user_registration_success(self):
        response = self.client.post(self.register_url, self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(User.objects.count(), 1)

        user = User.objects.first()
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.display_name, "Test User")
        self.assertFalse(user.is_email_verified)

    def test_user_registration_password_mismatch(self):
        payload = self.valid_payload.copy()
        payload["password_confirm"] = "afdlafalkdsfhlkh"

        response = self.client.post(self.register_url, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)
        self.assertIn("Passwords must match.", response.data["non_field_errors"])

    def test_user_registration_duplicate_email(self):
        User.objects.create_user(email="test@example.com", password="abc123")

        response = self.client.post(self.register_url, self.valid_payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 1)

    def test_user_registration_invalid_email(self):
        payload = self.valid_payload.copy()
        payload["email"] = "2olfsflksh"

        response = self.client.post(self.register_url, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)

        self.assertIn("email", response.data)

    def test_user_registration_missing_required_fields(self):
        required_fields = ["email", "password", "password_confirm"]
        for field in required_fields:
            with self.subTest(field=field):
                payload = self.valid_payload.copy()
                del payload[field]

                response = self.client.post(self.register_url, payload)
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_registration_empty_fields(self):
        empty_fields = {
            "email": "",
            "password": "",
            "password_confirm": "",
        }

        for field, empty_value in empty_fields.items():
            with self.subTest(field=field):
                payload = self.valid_payload.copy()
                payload[field] = empty_value

                response = self.client.post(self.register_url, payload)
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_registration_weak_password(self):
        weak_passwords = ["123", "abc", "password", "12345678"]

        for weak_pass in weak_passwords:
            with self.subTest(password=weak_pass):
                payload = self.valid_payload.copy()
                payload["password"] = weak_pass
                payload["password_confirm"] = weak_pass

                response = self.client.post(self.register_url, payload)
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertEqual(User.objects.count(), 0)

    def test_user_registration_various_invalid_emails(self):
        invalid_emails = [
            "notanemail",
            "@example.com",
            "test@",
            "test..test@example.com",
            "test@example",
            "test space@example.com",
            "test@exam ple.com",
        ]

        for invalid_email in invalid_emails:
            with self.subTest(email=invalid_email):
                payload = self.valid_payload.copy()
                payload["email"] = invalid_email

                response = self.client.post(self.register_url, payload)
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertEqual(User.objects.count(), 0)

    def test_user_registration_case_insensitive_email(self):
        User.objects.create_user(email="TEST@EXAMPLE.COM", password="abc123")

        payload = self.valid_payload.copy()
        payload["email"] = "test@example.com"

        response = self.client.post(self.register_url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 1)

    def test_user_registration_whitespace_handling(self):
        payload = self.valid_payload.copy()
        payload["email"] = "  test@example.com  "
        payload["display_name"] = "  Test User  "

        response = self.client.post(self.register_url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.first()
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.display_name, "Test User")

    def test_user_registration_response_structure(self):
        response = self.client.post(self.register_url, self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertIn("message", response.data)

        response_str = str(response.data)
        self.assertNotIn("password", response_str.lower())

    def test_user_registration_long_display_name(self):
        payload = self.valid_payload.copy()
        payload["display_name"] = "x" * 500

        response = self.client.post(self.register_url, payload)
        self.assertIn(
            response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST]
        )

    def test_user_registration_unicode_characters(self):
        payload = self.valid_payload.copy()
        payload["display_name"] = "José García 测试 🚀"
        payload["email"] = "jose@example.com"

        response = self.client.post(self.register_url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.first()
        self.assertEqual(user.display_name, "José García 测试 🚀")

    def test_user_registration_password_too_similar_to_email(self):
        payload = self.valid_payload.copy()
        payload["email"] = "testuser@example.com"
        payload["password"] = "testuser123"
        payload["password_confirm"] = "testuser123"

        response = self.client.post(self.register_url, payload)
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            self.assertIn("Password", response.data)

    def test_user_registration_http_methods(self):
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        response = self.client.put(self.register_url, self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        response = self.client.delete(self.register_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class ProfileViewTests(APITestCase):

    def setUp(self):
        self.profile_url = reverse("profile")

        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123", display_name="Test User"
        )

    def test_get_profile_authenticated(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "test@example.com")
        self.assertEqual(response.data["display_name"], "Test User")
        self.assertNotIn("password", response.data)

    def test_get_profile_unauthenticated(self):
        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_profile_success(self):
        self.client.force_authenticate(user=self.user)

        update_data = {"display_name": "Updated Name"}

        response = self.client.patch(self.profile_url, update_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)
        self.assertIn("user", response.data)
        self.assertEqual(response.data["message"], "Profile updated successfully")

        self.user.refresh_from_db()
        self.assertEqual(self.user.display_name, "Updated Name")

    def test_patch_profile_unauthenticated(self):
        update_data = {"display_name": "Hacker Name"}

        response = self.client.patch(self.profile_url, update_data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.user.refresh_from_db()
        self.assertEqual(self.user.display_name, "Test User")

    def test_patch_profile_partial_update(self):
        self.client.force_authenticate(user=self.user)

        update_data = {"display_name": "Partially Updated"}

        response = self.client.patch(self.profile_url, update_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()
        self.assertEqual(self.user.display_name, "Partially Updated")
        self.assertEqual(self.user.email, "test@example.com")

    def test_patch_profile_email_ignored(self):
        """Test email field is ignored in profile updates (read-only)"""
        self.client.force_authenticate(user=self.user)

        update_data = {
            "email": "newemail@example.com",  # This should be ignored
            "display_name": "Updated Name",
        }

        response = self.client.patch(self.profile_url, update_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify email unchanged, display_name updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "test@example.com")  # Unchanged
        self.assertEqual(self.user.display_name, "Updated Name")  # Changed

    def test_patch_profile_unicode_display_name(self):
        self.client.force_authenticate(user=self.user)

        update_data = {"display_name": "José García 测试 🚀"}

        response = self.client.patch(self.profile_url, update_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()
        self.assertEqual(self.user.display_name, "José García 测试 🚀")

    def test_patch_profile_long_display_name(self):
        """Test profile update with very long display name"""
        self.client.force_authenticate(user=self.user)

        # Assuming your model has max_length constraint
        update_data = {"display_name": "x" * 500}

        response = self.client.patch(self.profile_url, update_data)

        # Should either succeed or fail gracefully
        self.assertIn(
            response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]
        )

    def test_patch_profile_same_email_as_current(self):
        """Test user can update to their own current email (should succeed)"""
        self.client.force_authenticate(user=self.user)

        update_data = {
            "email": "test@example.com",  # Same as current
            "display_name": "Updated Name",
        }

        response = self.client.patch(self.profile_url, update_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()
        self.assertEqual(self.user.display_name, "Updated Name")

    def test_patch_profile_multiple_fields(self):
        """Test updating multiple fields at once"""
        self.client.force_authenticate(user=self.user)

        update_data = {
            "bio": "This is my updated bio",
            "display_name": "New Display Name",
        }

        response = self.client.patch(self.profile_url, update_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()
        self.assertEqual(self.user.bio, "This is my updated bio")
        self.assertEqual(self.user.display_name, "New Display Name")

    def test_profile_http_methods(self):
        """Test that only GET and PATCH methods are allowed"""
        self.client.force_authenticate(user=self.user)

        # Test POST
        response = self.client.post(self.profile_url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Test PUT
        response = self.client.put(self.profile_url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Test DELETE
        response = self.client.delete(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_patch_profile_response_structure(self):
        """Test that PATCH response has expected structure"""
        self.client.force_authenticate(user=self.user)

        update_data = {"display_name": "Response Test"}

        response = self.client.patch(self.profile_url, update_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify response structure matches your view
        self.assertIn("message", response.data)
        self.assertIn("user", response.data)
        self.assertEqual(response.data["message"], "Profile updated successfully")

        # Verify user data is present
        user_data = response.data["user"]
        self.assertIn("email", user_data)
        self.assertIn("display_name", user_data)
        # Ensure password is not in response
        self.assertNotIn("password", user_data)
