from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
import uuid

User = get_user_model()


class CustomUserManagerTests(TestCase):

    def test_create_user_success(self):
        user = User.objects.create_user(
            email="test@example.com", password="testpass123", display_name="Test User"
        )

        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.display_name, "Test User")
        self.assertTrue(user.check_password("testpass123"))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_email_verified)

    def test_create_user_without_email(self):
        """Test creating user without email raises ValueError"""
        with self.assertRaises(ValueError) as context:
            User.objects.create_user(email="", password="testpass123")

        self.assertEqual(str(context.exception), "Email is required")

    def test_create_user_without_password(self):
        user = User.objects.create_user(email="test@example.com")

        self.assertEqual(user.email, "test@example.com")
        self.assertFalse(user.has_usable_password())

    def test_create_user_normalizes_email(self):
        user = User.objects.create_user(
            email="test@EXAMPLE.COM", password="testpass123"
        )

        self.assertEqual(user.email, "test@example.com")

    def test_create_user_with_extra_fields(self):
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            display_name="Custom Name",
            phone="+1234567890",
            bio="Test bio",
        )

        self.assertEqual(user.display_name, "Custom Name")
        self.assertEqual(user.phone, "+1234567890")
        self.assertEqual(user.bio, "Test bio")

    def test_create_superuser_success(self):
        user = User.objects.create_superuser(
            email="admin@example.com", password="adminpass123"
        )

        self.assertEqual(user.email, "admin@example.com")
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_email_verified)

    def test_create_superuser_without_is_staff(self):
        with self.assertRaises(ValueError) as context:
            User.objects.create_superuser(
                email="admin@example.com", password="adminpass123", is_staff=False
            )

        self.assertEqual(str(context.exception), "Superuser must have is_staff=True")

    def test_create_superuser_without_is_superuser(self):
        with self.assertRaises(ValueError) as context:
            User.objects.create_superuser(
                email="admin@example.com", password="adminpass123", is_superuser=False
            )

        self.assertEqual(
            str(context.exception), "Superuser must have is_superuser=True"
        )


class CustomUserModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com", password="testpass123", display_name="Test User"
        )

    def test_user_string_representation(self):
        expected = "Test User (test@example.com)"
        self.assertEqual(str(self.user), expected)

    def test_user_string_with_default_display_name(self):
        user = User.objects.create_user(email="default@example.com", password="pass123")
        expected = "User (default@example.com)"
        self.assertEqual(str(user), expected)

    def test_user_has_uuid_primary_key(self):
        self.assertIsInstance(self.user.id, uuid.UUID)

    def test_uuid_is_unique(self):
        user2 = User.objects.create_user(
            email="test2@example.com", password="testpass123"
        )

        self.assertNotEqual(self.user.id, user2.id)

    def test_email_is_unique(self):
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                email="test@example.com", password="anotherpass123"  # Same email
            )

    def test_email_max_length(self):
        long_email = "a" * 250 + "@example.com"
        user = User(email=long_email, password="testpass123")

        with self.assertRaises(ValidationError):
            user.full_clean()

    def test_display_name_max_length(self):
        long_name = "x" * 76  # Over 75 chars
        user = User(email="test@example.com", display_name=long_name)

        with self.assertRaises(ValidationError):
            user.full_clean()

    def test_phone_can_be_blank(self):
        self.assertIsNone(self.user.phone)

    def test_phone_max_length(self):
        long_phone = "1" * 21  # Over 20 chars
        user = User(email="test@example.com", phone=long_phone)

        with self.assertRaises(ValidationError):
            user.full_clean()

    def test_bio_can_be_blank(self):
        self.assertIsNone(self.user.bio)

    def test_bio_max_length(self):
        long_bio = "x" * 501  # Over 500 chars
        user = User(email="test@example.com", bio=long_bio)

        with self.assertRaises(ValidationError):
            user.full_clean()

    def test_is_email_verified_default(self):
        self.assertFalse(self.user.is_email_verified)

    def test_avatar_can_be_blank(self):
        self.assertFalse(self.user.avatar)

    def test_username_field_is_email(self):
        self.assertEqual(User.USERNAME_FIELD, "email")

    def test_required_fields_empty(self):
        self.assertEqual(User.REQUIRED_FIELDS, [])

    def test_username_field_does_not_exist(self):
        with self.assertRaises(Exception):
            User._meta.get_field("username")

    def test_unicode_in_display_name(self):
        user = User.objects.create_user(
            email="unicode@example.com",
            password="testpass123",
            display_name="José García 测试 🚀",
        )

        self.assertEqual(user.display_name, "José García 测试 🚀")

    def test_unicode_in_bio(self):
        user = User.objects.create_user(
            email="unicode@example.com",
            password="testpass123",
            bio="This is a bio with unicode: José García 测试 🚀",
        )

        self.assertEqual(user.bio, "This is a bio with unicode: José García 测试 🚀")

    def test_user_authentication_works(self):
        from django.contrib.auth import authenticate

        user = authenticate(email="test@example.com", password="testpass123")
        self.assertEqual(user, self.user)

    def test_user_authentication_fails_wrong_password(self):
        from django.contrib.auth import authenticate

        user = authenticate(email="test@example.com", password="wrongpass")
        self.assertIsNone(user)

    def test_user_authentication_fails_wrong_email(self):
        from django.contrib.auth import authenticate

        user = authenticate(email="wrong@example.com", password="testpass123")
        self.assertIsNone(user)
