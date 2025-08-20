# Pingo - Real-time Chat Platform

Discord-like chat application with servers, channels, and real-time messaging.

## Current Status

🚧 **Phase 1 Development** - Building core MVP features

## Features (Completed)

- [x] Project setup with Docker
- [x] User authentication - JWT based auth system
- [x] CI pipeline using Github Actions
- [x] Postman API Collection(authentication)
- [ ] Real-time messaging
- [ ] Server/channel creation

## Documentation

### API Documentation

- [Authentication](./docs/authentication.md) - Complete authentication API reference

## Quick Start

```bash
# Clone repository
git clone https://github.com/your-username/pingo.git
cd pingo

# Start development environment
docker-compose up -d
```

## API Endpoints

**Authentication**: `http://127.0.0.1:8000/api/auth/`

- Registration, login, profile management
- JWT token-based authentication
- See [Authentication Docs](./docs/authentication.md) for details

## Development
