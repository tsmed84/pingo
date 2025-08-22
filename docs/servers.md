# Server & Membership Management API

Complete API reference for Pingo's Discord-like server and membership system.

## Base URL

```
http://127.0.0.1:8000/api/servers/
```

## Authentication

All endpoints require JWT authentication. Include the token in your request headers:

```
Authorization: Bearer <your_jwt_token>
```

---

## Server Management

### List Servers

**GET** `/servers/`

Get list of servers with optional filtering.

#### Query Parameters

| Parameter     | Type   | Description                                                    | Example              |
| ------------- | ------ | -------------------------------------------------------------- | -------------------- |
| `member_type` | string | Filter by user's role: `owner`, `admin`, `moderator`, `member` | `?member_type=owner` |
| `visibility`  | string | Filter by visibility: `public`, `private`                      | `?visibility=public` |
| `search`      | string | Search servers by name (case-insensitive)                      | `?search=gaming`     |

#### Example Request

```bash
GET /api/servers/?member_type=owner&visibility=public&search=gaming
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

#### Example Response

```json
{
  "message": "Success",
  "servers": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Gaming Hub",
      "description": "A place for gamers to chat",
      "visibility": "public",
      "icon": null,
      "member_count": 12,
      "owner": {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "display_name": "John Doe",
        "email": "john@example.com"
      },
      "created": "2024-01-15T10:30:00Z",
      "updated": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### Create Server

**POST** `/servers/`

Create a new server. User automatically becomes owner.

#### Request Body

| Field         | Type   | Required | Description                               |
| ------------- | ------ | -------- | ----------------------------------------- |
| `name`        | string | Yes      | Server name (max 100 chars)               |
| `description` | string | No       | Server description                        |
| `visibility`  | string | No       | `public` or `private` (default: `public`) |
| `icon`        | file   | No       | Server icon image                         |

#### Example Request

```bash
POST /api/servers/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Content-Type: application/json

{
  "name": "My Gaming Server",
  "description": "A place for my friends to chat",
  "visibility": "private"
}
```

#### Example Response

```json
{
  "message": "Server created successfully",
  "server": {
    "id": "550e8400-e29b-41d4-a716-446655440002",
    "name": "My Gaming Server",
    "description": "A place for my friends to chat",
    "visibility": "private",
    "icon": null,
    "member_count": 1,
    "owner": {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "display_name": "John Doe",
      "email": "john@example.com"
    },
    "created": "2024-01-15T10:30:00Z",
    "updated": "2024-01-15T10:30:00Z"
  }
}
```

### Get Server Details

**GET** `/servers/{server_id}/`

Get detailed information about a specific server.

#### Permissions

- **Public servers**: Anyone can view
- **Private servers**: Only members and owner can view

#### Example Request

```bash
GET /api/servers/550e8400-e29b-41d4-a716-446655440000/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

#### Example Response

```json
{
  "message": "Success",
  "server": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Gaming Hub",
    "description": "A place for gamers to chat",
    "visibility": "public",
    "icon": null,
    "member_count": 12,
    "owner": {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "display_name": "John Doe",
      "email": "john@example.com"
    },
    "created": "2024-01-15T10:30:00Z",
    "updated": "2024-01-15T10:30:00Z"
  }
}
```

### Update Server

**PATCH** `/servers/{server_id}/`

Update server details. Only owners and admins can update servers.

#### Permissions

- **Owner**: Can update all fields
- **Admin**: Can update all fields

#### Request Body

| Field         | Type   | Description           |
| ------------- | ------ | --------------------- |
| `name`        | string | Server name           |
| `description` | string | Server description    |
| `visibility`  | string | `public` or `private` |
| `icon`        | file   | Server icon           |

#### Example Request

```bash
PATCH /api/servers/550e8400-e29b-41d4-a716-446655440000/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Content-Type: application/json

{
  "name": "Updated Gaming Hub",
  "description": "The best place for gamers"
}
```

#### Example Response

```json
{
  "message": "Server details updated successfully",
  "server": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Updated Gaming Hub",
    "description": "The best place for gamers",
    "visibility": "public",
    "icon": null,
    "member_count": 12,
    "owner": {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "display_name": "John Doe",
      "email": "john@example.com"
    },
    "created": "2024-01-15T10:30:00Z",
    "updated": "2024-01-15T12:45:00Z"
  }
}
```

### Delete Server

**DELETE** `/servers/{server_id}/`

Delete a server. Only the server owner can delete servers.

#### Permissions

- **Owner only**: Can delete the server

#### Example Request

```bash
DELETE /api/servers/550e8400-e29b-41d4-a716-446655440000/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

#### Example Response

```
Status: 204 No Content
```

---

## Membership Management

### List Server Members

**GET** `/servers/{server_id}/memberships/`

Get list of all members in a server.

#### Permissions

- **Members and Owner**: Can view member list
- **Non-members**: Cannot view private server members

#### Query Parameters

| Parameter | Type   | Description                                             | Example        |
| --------- | ------ | ------------------------------------------------------- | -------------- |
| `role`    | string | Filter by role: `owner`, `admin`, `moderator`, `member` | `?role=admin`  |
| `search`  | string | Search members by display name                          | `?search=john` |

#### Example Request

```bash
GET /api/servers/550e8400-e29b-41d4-a716-446655440000/memberships/?role=admin
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

#### Example Response

```json
{
  "message": "Success",
  "memberships": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440003",
      "user": {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "display_name": "John Doe",
        "email": "john@example.com"
      },
      "server": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Gaming Hub",
        "visibility": "public"
      },
      "role": "owner",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### Join Server

**POST** `/servers/{server_id}/memberships/`

Join a server as a new member.

#### Request Body

| Field         | Type   | Required            | Description                  |
| ------------- | ------ | ------------------- | ---------------------------- |
| `invite_code` | string | For private servers | Required for private servers |

#### Business Rules

- Cannot join if already a member
- Server owner cannot join their own server
- Private servers require valid invite code

#### Example Request (Public Server)

```bash
POST /api/servers/550e8400-e29b-41d4-a716-446655440000/memberships/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Content-Type: application/json

{}
```

#### Example Request (Private Server)

```bash
POST /api/servers/550e8400-e29b-41d4-a716-446655440000/memberships/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Content-Type: application/json

{
  "invite_code": "SECRET123"
}
```

#### Example Response

```json
{
  "message": "Congratulations! You have joined Gaming Hub.",
  "membership": {
    "id": "550e8400-e29b-41d4-a716-446655440004",
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440002",
      "display_name": "Jane Smith",
      "email": "jane@example.com"
    },
    "server": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Gaming Hub",
      "visibility": "public"
    },
    "role": "member",
    "created_at": "2024-01-15T11:00:00Z",
    "updated_at": "2024-01-15T11:00:00Z"
  }
}
```

### Get Member Details

**GET** `/servers/{server_id}/members/{user_id}/`

Get details about a specific member in a server.

#### Permissions

- **Self**: Can view own membership
- **Owner**: Can view any membership
- **Admin**: Can view any membership

#### Example Request

```bash
GET /api/servers/550e8400-e29b-41d4-a716-446655440000/members/550e8400-e29b-41d4-a716-446655440002/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

#### Example Response

```json
{
  "message": "Success",
  "membership": {
    "id": "550e8400-e29b-41d4-a716-446655440004",
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440002",
      "display_name": "Jane Smith",
      "email": "jane@example.com"
    },
    "server": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Gaming Hub",
      "visibility": "public"
    },
    "role": "member",
    "created_at": "2024-01-15T11:00:00Z",
    "updated_at": "2024-01-15T11:00:00Z"
  }
}
```

### Update Member Role

**PATCH** `/servers/{server_id}/members/{user_id}/`

Update a member's role in the server.

#### Permissions

- **Owner**: Can update any member's role
- **Admin**: Can update any member's role (except owner)

#### Request Body

| Field  | Type   | Required | Description                       |
| ------ | ------ | -------- | --------------------------------- |
| `role` | string | Yes      | `admin`, `moderator`, or `member` |

#### Business Rules

- Cannot modify owner's role
- Users cannot change their own role
- Only `role` field can be updated

#### Example Request

```bash
PATCH /api/servers/550e8400-e29b-41d4-a716-446655440000/members/550e8400-e29b-41d4-a716-446655440002/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Content-Type: application/json

{
  "role": "admin"
}
```

#### Example Response

```json
{
  "message": "Member role updated successfully.",
  "membership": {
    "id": "550e8400-e29b-41d4-a716-446655440004",
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440002",
      "display_name": "Jane Smith",
      "email": "jane@example.com"
    },
    "server": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Gaming Hub",
      "visibility": "public"
    },
    "role": "admin",
    "created_at": "2024-01-15T11:00:00Z",
    "updated_at": "2024-01-15T12:00:00Z"
  }
}
```

### Remove Member / Leave Server

**DELETE** `/servers/{server_id}/members/{user_id}/`

Remove a member from the server or leave the server yourself.

#### Permissions

- **Self**: Can leave the server
- **Owner**: Can remove any member
- **Admin**: Can remove any member (except owner)

#### Business Rules

- Server owner cannot leave their own server
- Admin cannot remove the server owner

#### Example Request (Leave Server)

```bash
DELETE /api/servers/550e8400-e29b-41d4-a716-446655440000/members/550e8400-e29b-41d4-a716-446655440002/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

#### Example Response (Self-Leave)

```json
{
  "message": "You have left Gaming Hub."
}
```

#### Example Response (Admin Removal)

```json
{
  "message": "Jane Smith has been removed from Gaming Hub."
}
```

---

## Error Responses

### Common HTTP Status Codes

| Code  | Description                          |
| ----- | ------------------------------------ |
| `200` | Success                              |
| `201` | Created                              |
| `400` | Bad Request (validation errors)      |
| `401` | Unauthorized (missing/invalid token) |
| `403` | Forbidden (insufficient permissions) |
| `404` | Not Found (resource doesn't exist)   |

### Error Response Format

```json
{
  "error": "Human-readable error message",
  "details": {
    "field_name": ["Specific validation error"]
  }
}
```

### Common Error Examples

#### Validation Error (400)

```json
{
  "error": "Failed to create server.",
  "details": {
    "name": ["This field is required."],
    "visibility": ["\"invalid\" is not a valid choice."]
  }
}
```

#### Permission Denied (403)

```json
{
  "error": "Permission denied. You are not a member of this server."
}
```

#### Not Found (404)

```json
{
  "error": "Server does not exist."
}
```

---

## Role Hierarchy

Understanding the permission system:

| Role          | Permissions                                               |
| ------------- | --------------------------------------------------------- |
| **Owner**     | Full control: manage server, all members, delete server   |
| **Admin**     | Manage server settings, manage members (except owner)     |
| **Moderator** | Basic moderation (future: manage channels, moderate chat) |
| **Member**    | Basic access: view content, participate in chat           |

---

## Rate Limiting

Currently no rate limiting is implemented. This will be added in future versions.

---

## Changelog

- **v1.0** (Issue #3): Initial server and membership management API
