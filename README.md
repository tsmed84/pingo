# Pingo - Real-time Chat Platform

Discord-like chat application with servers, channels, and real-time messaging.

## Current Status

🚧 **Phase 1 Development** - Building core MVP features

### Completed Issues

- ✅ **Issue #1**: Backend Setup (Django + Channels + DRF + Docker)
- ✅ **Issue #2**: Authentication System (Custom User + JWT + GitHub Actions CI)
- ✅ **Issue #3**: Server Models & Membership Management API
- 🔄 **Issue #4**: Channel Models & Messaging (Next)

## Features (Completed)

- [x] Project setup with Docker
- [x] User authentication - JWT based auth system
- [x] CI pipeline using Github Actions
- [x] Server management - Create, join, and manage Discord-like servers
- [x] Membership system - Role-based access control (owner/admin/moderator/member)
- [x] Public/Private servers with invite codes
- [ ] Channel creation and management
- [ ] Real-time messaging
- [ ] Direct messaging

## Documentation

### API Documentation

- [Authentication](./docs/authentication.md) - Complete authentication API reference
- [Servers & Membership](./docs/servers.md) - Server management and member operations

## Quick Start

```bash
# Clone repository
git clone https://github.com/your-username/pingo.git
cd pingo

# Start development environment
docker-compose up -d

# Run tests
docker-compose exec backend python manage.py test

## API Endpoints
#### Base URL: http://127.0.0.1:8000/api/
#### Authentication: /auth/

Registration, login, profile management
JWT token-based authentication
See Authentication Docs for details

#### Servers & Membership: /servers/

Server CRUD operations with role-based permissions
Member management (join, leave, promote, remove)
Public/private servers with invite codes
See Server Docs for complete reference

## Tech Stack

Backend: Django 4.x, Django REST Framework, Channels
Database: PostgreSQL, Redis
Authentication: JWT tokens
CI/CD: GitHub Actions
Containerization: Docker & Docker Compose
```
