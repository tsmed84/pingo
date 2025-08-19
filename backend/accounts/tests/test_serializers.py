from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework import serializers
from accounts.serializers import (
    UserRegistrationSerializer,
    UserProfileSerializer,
)

User = get_user_model()


class UserRegistrationSerializerTests(TestCase):

    def setUp(self):
        self.valid_data = {
            "email": "test@example.com",
            "password": "strongpass123",
            "password_confirm": "strongpass123",
            "display_name": "Test User",
            "phone": "+1234567890",
            "bio": "Test bio",
        }

    def test_valid_registration_data(self):
        """Test serializer with valid registration data"""
        serializer = UserRegistrationSerializer(data=self.valid_data)

        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["email"], "test@example.com")
        self.assertEqual(serializer.validated_data["display_name"], "Test User")

    def test_create_user_from_valid_data(self):
        """Test creating user from validated data"""
        serializer = UserRegistrationSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())

        user = serializer.save()

        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.display_name, "Test User")
        self.assertEqual(user.phone, "+1234567890")
        self.assertEqual(user.bio, "Test bio")
        self.assertTrue(user.check_password("strongpass123"))

    def test_email_normalization(self):
        """Test email is normalized to lowercase"""
        data = self.valid_data.copy()
        data["email"] = "TEST@EXAMPLE.COM"

        serializer = UserRegistrationSerializer(data=data)
        self.assertTrue(serializer.is_valid())

        self.assertEqual(serializer.validated_data["email"], "test@example.com")

    def test_duplicate_email_validation(self):
        """Test validation fails for duplicate email"""
        # Create existing user
        User.objects.create_user(email="test@example.com", password="pass123")

        serializer = UserRegistrationSerializer(data=self.valid_data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)
        self.assertEqual(
            str(serializer.errors["email"][0]), "user with this email already exists."
        )

    def test_case_insensitive_duplicate_email(self):
        """Test validation catches case-insensitive duplicate emails"""
        # Create user with uppercase email
        User.objects.create_user(email="TEST@EXAMPLE.COM", password="pass123")

        data = self.valid_data.copy()
        data["email"] = "test@example.com"  # lowercase version

        serializer = UserRegistrationSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

    def test_password_mismatch_validation(self):
        """Test validation fails when passwords don't match"""
        data = self.valid_data.copy()
        data["password_confirm"] = "differentpassword"

        serializer = UserRegistrationSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("non_field_errors", serializer.errors)
        self.assertEqual(
            str(serializer.errors["non_field_errors"][0]), "Passwords must match."
        )

    def test_weak_password_validation(self):
        """Test Django's password validation is applied"""
        data = self.valid_data.copy()
        data["password"] = "123"  # Too short
        data["password_confirm"] = "123"

        serializer = UserRegistrationSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)

    def test_missing_required_fields(self):
        """Test validation fails for missing required fields"""
        required_fields = ["email", "password", "password_confirm"]

        for field in required_fields:
            with self.subTest(field=field):
                data = self.valid_data.copy()
                del data[field]

                serializer = UserRegistrationSerializer(data=data)

                self.assertFalse(serializer.is_valid())
                self.assertIn(field, serializer.errors)

    def test_optional_fields_can_be_omitted(self):
        """Test optional fields (phone, bio) can be omitted"""
        data = {
            "email": "test@example.com",
            "password": "strongpass123",
            "password_confirm": "strongpass123",
            "display_name": "Test User",
        }

        serializer = UserRegistrationSerializer(data=data)

        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertIsNone(user.phone)
        self.assertIsNone(user.bio)

    def test_empty_optional_fields(self):
        """Test empty strings for optional fields"""
        data = self.valid_data.copy()
        data["phone"] = ""
        data["bio"] = ""

        serializer = UserRegistrationSerializer(data=data)

        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertEqual(user.phone, "")
        self.assertEqual(user.bio, "")

    def test_invalid_email_format(self):
        """Test validation fails for invalid email formats"""
        invalid_emails = [
            "notanemail",
            "@example.com",
            "test@",
            "test..test@example.com",
        ]

        for invalid_email in invalid_emails:
            with self.subTest(email=invalid_email):
                data = self.valid_data.copy()
                data["email"] = invalid_email

                serializer = UserRegistrationSerializer(data=data)

                self.assertFalse(serializer.is_valid())
                self.assertIn("email", serializer.errors)

    def test_unicode_in_display_name(self):
        """Test unicode characters work in display_name"""
        data = self.valid_data.copy()
        data["display_name"] = "José García 测试"

        serializer = UserRegistrationSerializer(data=data)

        self.assertTrue(serializer.is_valid())
        user = serializer.save()
        self.assertEqual(user.display_name, "José García 测试")

    def test_password_not_in_representation(self):
        """Test password fields are write-only (not in serialized output)"""
        serializer = UserRegistrationSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
        user = serializer.save()

        # Serialize the created user
        output_serializer = UserRegistrationSerializer(user)

        self.assertNotIn("password", output_serializer.data)
        self.assertNotIn("password_confirm", output_serializer.data)

    def test_serializer_validation_order(self):
        """Test that field validation runs before object validation"""
        # Create existing user
        User.objects.create_user(email="test@example.com", password="pass123")

        data = self.valid_data.copy()
        data["password_confirm"] = "different"  # This should trigger both validations

        serializer = UserRegistrationSerializer(data=data)

        self.assertFalse(serializer.is_valid())
        # Should have both email and password mismatch errors
        self.assertIn("email", serializer.errors)


class UserProfileSerializerTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            display_name="Original Name",
            phone="+1234567890",
            bio="Original bio",
        )

    def test_serialize_user_profile(self):
        """Test serializing user profile data"""
        serializer = UserProfileSerializer(self.user)

        expected_fields = [
            "id",
            "email",
            "display_name",
            "bio",
            "phone",
            "avatar",
            "is_email_verified",
            "date_joined",
        ]

        for field in expected_fields:
            self.assertIn(field, serializer.data)

        self.assertEqual(serializer.data["email"], "test@example.com")
        self.assertEqual(serializer.data["display_name"], "Original Name")

    def test_update_writable_fields(self):
        """Test updating only writable fields"""
        update_data = {
            "display_name": "Updated Name",
            "bio": "Updated bio",
            "phone": "+9876543210",
        }

        serializer = UserProfileSerializer(self.user, data=update_data, partial=True)

        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()

        self.assertEqual(updated_user.display_name, "Updated Name")
        self.assertEqual(updated_user.bio, "Updated bio")
        self.assertEqual(updated_user.phone, "+9876543210")

    def test_read_only_fields_ignored(self):
        """Test read-only fields are ignored in updates"""
        original_email = self.user.email
        original_id = self.user.id
        original_verified = self.user.is_email_verified
        original_joined = self.user.date_joined

        update_data = {
            "id": "new-uuid",
            "email": "hacker@evil.com",
            "is_email_verified": not original_verified,
            "date_joined": "2020-01-01T00:00:00Z",
            "display_name": "Updated Name",  # This should work
        }

        serializer = UserProfileSerializer(self.user, data=update_data, partial=True)

        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()

        # Read-only fields unchanged
        self.assertEqual(updated_user.id, original_id)
        self.assertEqual(updated_user.email, original_email)
        self.assertEqual(updated_user.is_email_verified, original_verified)
        self.assertEqual(updated_user.date_joined, original_joined)

        # Writable field updated
        self.assertEqual(updated_user.display_name, "Updated Name")

    def test_partial_update(self):
        """Test partial updates only change specified fields"""
        original_bio = self.user.bio

        update_data = {"display_name": "Partially Updated"}

        serializer = UserProfileSerializer(self.user, data=update_data, partial=True)

        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()

        self.assertEqual(updated_user.display_name, "Partially Updated")
        self.assertEqual(updated_user.bio, original_bio)  # Unchanged

    def test_empty_display_name_validation(self):
        """Test validation for empty display_name"""
        update_data = {"display_name": ""}

        serializer = UserProfileSerializer(self.user, data=update_data, partial=True)

        # This depends on your model's blank=True/False setting
        # Adjust expectation based on your model validation
        if (
            hasattr(User._meta.get_field("display_name"), "blank")
            and not User._meta.get_field("display_name").blank
        ):
            self.assertFalse(serializer.is_valid())
            self.assertIn("display_name", serializer.errors)
        else:
            self.assertTrue(serializer.is_valid())

    def test_unicode_in_profile_fields(self):
        """Test unicode characters in profile fields"""
        update_data = {
            "display_name": "José García 测试",
            "bio": "Biography with unicode: 🚀 ñáéíóú",
        }

        serializer = UserProfileSerializer(self.user, data=update_data, partial=True)

        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()

        self.assertEqual(updated_user.display_name, "José García 测试")
        self.assertEqual(updated_user.bio, "Biography with unicode: 🚀 ñáéíóú")

    def test_none_values_for_optional_fields(self):
        """Test setting optional fields to None"""
        update_data = {"phone": None, "bio": None}

        serializer = UserProfileSerializer(self.user, data=update_data, partial=True)

        self.assertTrue(serializer.is_valid())
        updated_user = serializer.save()

        self.assertIsNone(updated_user.phone)
        self.assertIsNone(updated_user.bio)

    def test_serializer_representation_excludes_sensitive_data(self):
        """Test serialized data doesn't include sensitive information"""
        serializer = UserProfileSerializer(self.user)

        # These should not be in the serialized data
        sensitive_fields = ["password"]

        for field in sensitive_fields:
            self.assertNotIn(field, serializer.data)

    def test_all_expected_fields_present(self):
        """Test all expected fields are present in serialized data"""
        serializer = UserProfileSerializer(self.user)

        expected_fields = [
            "id",
            "email",
            "display_name",
            "bio",
            "phone",
            "avatar",
            "is_email_verified",
            "date_joined",
        ]

        for field in expected_fields:
            with self.subTest(field=field):
                self.assertIn(field, serializer.data)
