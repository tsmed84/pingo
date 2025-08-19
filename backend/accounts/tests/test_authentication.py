from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError
import json

User = get_user_model()


class JWTAuthenticationTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123", display_name="Test User"
        )
        self.token_obtain_url = reverse("login")
        self.token_refresh_url = reverse("refresh")
        self.profile_url = reverse("profile")

    def test_obtain_jwt_token_with_valid_credentials(self):
        data = {"email": "test@example.com", "password": "testpass123"}

        response = self.client.post(self.token_obtain_url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

        # Verify tokens are not empty
        self.assertIsNotNone(response.data["access"])
        self.assertIsNotNone(response.data["refresh"])

    def test_obtain_token_with_invalid_email(self):
        data = {"email": "wrong@example.com", "password": "testpass123"}

        response = self.client.post(self.token_obtain_url, data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn("access", response.data)

    def test_obtain_token_with_invalid_password(self):
        data = {"email": "test@example.com", "password": "wrongpassword"}

        response = self.client.post(self.token_obtain_url, data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn("access", response.data)

    def test_obtain_token_with_missing_credentials(self):
        # Missing password
        data = {"email": "test@example.com"}
        response = self.client.post(self.token_obtain_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Missing email
        data = {"password": "testpass123"}
        response = self.client.post(self.token_obtain_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_access_protected_view_with_valid_token(self):
        # First, get a token
        data = {"email": "test@example.com", "password": "testpass123"}
        token_response = self.client.post(self.token_obtain_url, data)
        access_token = token_response.data["access"]

        # Use token to access protected view
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "test@example.com")

    def test_access_protected_view_without_token(self):
        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_protected_view_with_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalid.token.here")
        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_protected_view_with_malformed_token(self):
        # Missing Bearer prefix
        self.client.credentials(HTTP_AUTHORIZATION="invalidtoken")
        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token_functionality(self):
        # Get initial tokens
        data = {"email": "test@example.com", "password": "testpass123"}
        token_response = self.client.post(self.token_obtain_url, data)
        refresh_token = token_response.data["refresh"]

        # Use refresh token to get new access token
        refresh_data = {"refresh": refresh_token}
        refresh_response = self.client.post(self.token_refresh_url, refresh_data)

        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn("access", refresh_response.data)

        # New access token should work
        new_access_token = refresh_response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {new_access_token}")
        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_refresh_with_invalid_token(self):
        refresh_data = {"refresh": "invalid.refresh.token"}
        response = self.client.post(self.token_refresh_url, refresh_data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_contains_user_info(self):
        # Get tokens
        data = {"email": "test@example.com", "password": "testpass123"}
        response = self.client.post(self.token_obtain_url, data)
        access_token = response.data["access"]

        # Decode token to check contents (without verification for testing)
        from rest_framework_simplejwt.tokens import UntypedToken
        from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

        try:
            # This validates and decodes the token
            token = UntypedToken(access_token)
            self.assertIn("user_id", token.payload)
            self.assertEqual(str(token.payload["user_id"]), str(self.user.id))
        except (InvalidToken, TokenError):
            self.fail("Token should be valid and contain user information")


class JWTTokenModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123", display_name="Test User"
        )

    def test_generate_refresh_token_for_user(self):
        refresh = RefreshToken.for_user(self.user)

        # Token should contain user information
        self.assertEqual(refresh.payload["user_id"], str(self.user.id))
        self.assertIn("exp", refresh.payload)  # Expiration time
        self.assertIn("iat", refresh.payload)  # Issued at time

    def test_generate_access_token_from_refresh(self):
        refresh = RefreshToken.for_user(self.user)
        access = refresh.access_token

        # Access token should contain user information
        self.assertEqual(access.payload["user_id"], str(self.user.id))
        self.assertIn("exp", access.payload)
        self.assertIn("iat", access.payload)

    def test_token_validation(self):
        refresh = RefreshToken.for_user(self.user)
        access = refresh.access_token

        # Valid tokens should not raise exceptions
        try:
            # This will validate the token
            AccessToken(str(access))
            RefreshToken(str(refresh))
        except TokenError:
            self.fail("Valid tokens should not raise TokenError")

    def test_invalid_token_raises_error(self):
        with self.assertRaises(TokenError):
            AccessToken("invalid.token.string")

        with self.assertRaises(TokenError):
            RefreshToken("invalid.token.string")

    def test_expired_token_handling(self):
        # This test would require manipulating token expiration
        # For now, just test that the expiration field exists
        refresh = RefreshToken.for_user(self.user)
        access = refresh.access_token

        self.assertIn("exp", access.payload)
        self.assertIn("exp", refresh.payload)

        # Expiration should be in the future
        import time

        current_time = int(time.time())
        self.assertGreater(access.payload["exp"], current_time)
        self.assertGreater(refresh.payload["exp"], current_time)
