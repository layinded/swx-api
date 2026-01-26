# Development Guide

**Version:** 1.0.0  
**Last Updated:** 2026-01-26

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Setup](#setup)
4. [Development Workflow](#development-workflow)
5. [Code Quality](#code-quality)
6. [Testing](#testing)
7. [Database Migrations](#database-migrations)
8. [CLI Commands](#cli-commands)
9. [Hot Reloading](#hot-reloading)
10. [Troubleshooting](#troubleshooting)

---

## Overview

This guide covers **development setup and workflows** for SwX-API. For comprehensive development documentation, see the [Getting Started Guide](docs/02-getting-started/GETTING_STARTED.md).

---

## Prerequisites

### Required

- **Python 3.10+** - Check with `python --version`
- **PostgreSQL 12+** - Database server
- **Redis 6+** - Caching and rate limiting
- **Git** - Version control

### Optional

- **Docker & Docker Compose** - Containerized development
- **uv** - Fast Python package manager (alternative to pip)
- **VS Code** or **PyCharm** - IDE with Python support

---

## Setup

### Option 1: Docker (Recommended)

**Fastest setup for development:**

```bash
# Clone repository
git clone <repository-url>
cd swx-api-latest-backend

# Copy environment file
cp .env.example .env

# Edit .env with your configuration
# Then start services
docker compose up -d

# Application will be available at:
# - API: http://localhost:8001/api
# - Docs: http://localhost:8001/docs
```

**Docker services:**
- `swx-api` - FastAPI application (port 8001)
- `postgres` - PostgreSQL database (port 5432)
- `redis` - Redis cache (port 6379)

### Option 2: Local Development

**For development without Docker:**

```bash
# Clone repository
git clone <repository-url>
cd swx-api-latest-backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Or using uv (faster)
uv venv
uv pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env with your configuration
# Set DATABASE_URL and REDIS_URL to your local services

# Run database migrations
alembic upgrade head

# Start development server
uvicorn swx_core.main:app --reload --host 0.0.0.0 --port 8001
```

### Environment Configuration

**Required variables in `.env`:**

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/swx_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Secrets
SECRET_KEY=your-secret-key-here
ADMIN_SECRET_KEY=your-admin-secret-key-here

# Admin User
FIRST_SUPERUSER=admin@example.com
FIRST_SUPERUSER_PASSWORD=securepassword
```

**Optional variables:**

```env
# Email
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=user@example.com
SMTP_PASSWORD=password

# OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Monitoring
SENTRY_DSN=your-sentry-dsn
```

---

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

- Write code in `swx_app/` for application features
- Extend `swx_core/` for framework features
- Follow existing patterns and structure

### 3. Run Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest swx_core/tests/services/test_auth_service.py

# Run with coverage
pytest --cov=swx_core --cov=swx_app
```

### 4. Check Code Quality

```bash
# Format code
swx format

# Lint code
swx lint

# Type check
mypy swx_core swx_app
```

### 5. Commit Changes

```bash
git add .
git commit -m "feat: add your feature description"
```

### 6. Push and Create PR

```bash
git push origin feature/your-feature-name
# Create pull request on GitHub
```

---

## Code Quality

### Formatting

**Using CLI:**
```bash
swx format
```

**Manual:**
```bash
# Format with ruff
ruff format swx_core swx_app

# Run pre-commit hooks
pre-commit run --all-files
```

### Linting

**Using CLI:**
```bash
swx lint
```

**Manual:**
```bash
# Lint with ruff
ruff check swx_core swx_app

# Type check with mypy
mypy swx_core swx_app
```

### Pre-commit Hooks

**Install hooks:**
```bash
pre-commit install
```

**Run hooks:**
```bash
pre-commit run --all-files
```

**Hooks include:**
- Code formatting (ruff)
- Linting (ruff)
- Type checking (mypy)
- Security checks (bandit)

---

## Testing

### Running Tests

**All tests:**
```bash
pytest
```

**Specific test:**
```bash
pytest swx_core/tests/services/test_auth_service.py::test_login_user_service_success
```

**With coverage:**
```bash
pytest --cov=swx_core --cov=swx_app --cov-report=html
```

### Test Types

**Unit Tests:**
- Test individual functions/methods
- Located in `swx_core/tests/` and `swx_app/tests/`
- Use fixtures for setup

**Integration Tests:**
- Test component interactions
- Test API routes
- Use TestClient for HTTP requests

**Acceptance Tests:**
- Test complete workflows
- Located in `scripts/full_user_simulation.py`
- Simulate real user scenarios

### Writing Tests

**Example unit test:**
```python
# swx_core/tests/services/test_auth_service.py
@pytest.mark.asyncio
async def test_login_user_service_success(test_db, mock_request):
    """Test successful user login."""
    user_create = UserCreate(
        email="test@example.com",
        password="password123"
    )
    user = await register_user_service(test_db, user_create, mock_request)
    
    form_data = OAuth2PasswordRequestForm(
        username=user.email,
        password="password123"
    )
    token = await login_user_service(test_db, form_data, mock_request)
    
    assert token.access_token is not None
    assert token.token_type == "bearer"
```

**Example integration test:**
```python
# swx_core/tests/routes/test_auth_routes.py
def test_login_endpoint(client, test_db):
    """Test login endpoint."""
    # Register user
    response = client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == 201
    
    # Login
    response = client.post("/api/auth/", data={
        "username": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
```

**See [Testing Guide](docs/09-testing/TESTING_GUIDE.md) for comprehensive testing documentation.**

---

## Database Migrations

### Creating Migrations

**Using CLI:**
```bash
swx db revision -m "add user table"
```

**Manual:**
```bash
alembic revision --autogenerate -m "add user table"
```

### Applying Migrations

**Using CLI:**
```bash
swx db migrate
```

**Manual:**
```bash
alembic upgrade head
```

### Rolling Back Migrations

```bash
# Rollback one revision
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision>
```

### Checking Migration Status

```bash
# Current revision
alembic current

# Migration history
alembic history
```

---

## CLI Commands

### Available Commands

**Database:**
```bash
swx db migrate          # Apply migrations
swx db revision -m "description"  # Create migration
swx db current         # Show current revision
swx db history         # Show migration history
```

**Code Generation:**
```bash
swx make:resource blog  # Generate resource (model, routes, etc.)
```

**Code Quality:**
```bash
swx format              # Format code
swx lint                # Lint code
```

**Utilities:**
```bash
swx tinker              # Interactive Python shell
```

**Help:**
```bash
swx --help              # Show all commands
swx <command> --help    # Show command help
```

---

## Hot Reloading

### Development Server

**With uvicorn:**
```bash
uvicorn swx_core.main:app --reload --host 0.0.0.0 --port 8001
```

**With Docker:**
```bash
# Hot reloading enabled by default in docker-compose.yml
docker compose up
```

### How It Works

- **File watching** - Automatically detects file changes
- **Auto-reload** - Restarts server on code changes
- **Fast refresh** - Minimal downtime during reload

### Limitations

- **Database migrations** - Must be applied manually
- **Environment variables** - Requires restart to take effect
- **Configuration changes** - May require restart

---

## Troubleshooting

### Common Issues

**1. Import Errors**
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

**2. Database Connection Failed**
```bash
# Check database is running
docker compose ps db

# Check connection string
echo $DATABASE_URL
```

**3. Redis Connection Failed**
```bash
# Check Redis is running
docker compose ps redis

# Test connection
docker compose exec redis redis-cli ping
```

**4. Migration Errors**
```bash
# Check current revision
alembic current

# Check for conflicts
alembic check

# Rollback if needed
alembic downgrade -1
```

### Getting Help

- **Documentation:** [docs/](docs/)
- **Troubleshooting:** [docs/10-troubleshooting/TROUBLESHOOTING.md](docs/10-troubleshooting/TROUBLESHOOTING.md)
- **FAQ:** [docs/10-troubleshooting/FAQ.md](docs/10-troubleshooting/FAQ.md)
- **Debugging:** [docs/10-troubleshooting/DEBUGGING.md](docs/10-troubleshooting/DEBUGGING.md)

---

## Next Steps

- Read [Getting Started Guide](docs/02-getting-started/GETTING_STARTED.md) for detailed setup
- Read [Testing Guide](docs/09-testing/TESTING_GUIDE.md) for testing patterns
- Read [Extending Guide](docs/07-extending/EXTENDING_SWX.md) for adding features
- Read [Architecture Guide](docs/03-architecture/ARCHITECTURE.md) for system design

---

**Status:** Development guide updated, ready for development use.
