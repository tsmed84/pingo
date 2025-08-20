# Pingo Authentication API

Complete API reference for Pingo's JWT-based authentication system.

## Overview

Pingo uses JWT (JSON Web Tokens) for stateless authentication. The authentication system provides user registration, login, profile management, and secure token-based access to protected endpoints.

**Base URL**: `http://127.0.0.1:8000/api/auth/`

## Authentication Flow

1. **Register** a new user account
2. **Login** to receive JWT tokens (access + refresh)
3. **Use access token** for authenticated requests
4. **Refresh token** when access token expires

## Endpoints

### User Registration

Create a new user account.

**Endpoint**: `POST /api/auth/register/`

**Request Body**:

```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "display_name": "John Doe",
  "phone": "+1234567890",
  "bio": "Software developer passionate about real-time applications"
}
```

**Response** (201 Created):

```json
{
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "display_name": "John Doe",
    "phone": "+1234567890",
    "bio": "Software developer passionate about real-time applications",
    "is_email_verified": false,
    "date_joined": "2025-01-20T10:30:00Z"
  },
  "message": "User registered successfully"
}
```

**Validation Rules**:

- Email must be unique and valid format
- Password must meet complexity requirements:
  - Minimum 8 characters
  - At least one uppercase letter
  - At least one lowercase letter
  - At least one digit
  - At least one special character

---

### User Login

Authenticate user and receive JWT tokens.

**Endpoint**: `POST /api/auth/token/`

**Request Body**:

```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response** (200 OK):

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Token Information**:

- **Access Token**: Valid for 1 hour, used for API authentication
- **Refresh Token**: Valid for 7 days, used to obtain new access tokens

---

### Refresh Token

Obtain a new access token using refresh token.

**Endpoint**: `POST /api/auth/token/refresh/`

**Request Body**:

```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Response** (200 OK):

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

---

### Get User Profile

Retrieve current user's profile information.

**Endpoint**: `GET /api/auth/profile/`

**Headers**:

```
Authorization: Bearer <access_token>
```

**Response** (200 OK):

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "display_name": "John Doe",
  "phone": "+1234567890",
  "bio": "Software developer passionate about real-time applications",
  "avatar": null,
  "is_email_verified": false,
  "date_joined": "2025-01-20T10:30:00Z",
  "last_login": "2025-01-20T15:45:00Z"
}
```

---

### Update User Profile

Update user profile information (partial updates supported).

**Endpoint**: `PATCH /api/auth/profile/`

**Headers**:

```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body** (partial update example):

```json
{
  "display_name": "John Smith",
  "bio": "Senior Software Engineer at TechCorp",
  "phone": "+1987654321"
}
```

**Response** (200 OK):

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "display_name": "John Smith",
  "phone": "+1987654321",
  "bio": "Senior Software Engineer at TechCorp",
  "avatar": null,
  "is_email_verified": false,
  "date_joined": "2025-01-20T10:30:00Z",
  "last_login": "2025-01-20T15:45:00Z"
}
```

**Updatable Fields**:

- `display_name`
- `bio`
- `phone`
- `avatar` (planned)

**Read-only Fields**:

- `id`, `email`, `is_email_verified`, `date_joined`, `last_login`

## Error Responses

### 400 Bad Request

```json
{
  "email": ["This field is required."],
  "password": ["Password must contain at least one uppercase letter."]
}
```

### 401 Unauthorized

```json
{
  "detail": "Given token not valid for any token type",
  "code": "token_not_valid",
  "messages": [
    {
      "token_class": "AccessToken",
      "token_type": "access",
      "message": "Token is invalid or expired"
    }
  ]
}
```

### 409 Conflict (Duplicate Email)

```json
{
  "email": ["A user with this email already exists."]
}
```

## Authentication Headers

All protected endpoints require the following header:

```
Authorization: Bearer <access_token>
```

## Future Enhancements

- **Email Verification**: Amazon SES integration for email verification
- **Password Reset**: Secure password reset flow
- **Token Blacklisting**: Secure logout implementation

---
