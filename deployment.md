# Deployment Guide

**Version:** 1.0.0  
**Last Updated:** 2026-01-26

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Deployment Options](#deployment-options)
4. [Docker Deployment](#docker-deployment)
5. [Production Configuration](#production-configuration)
6. [Environment Variables](#environment-variables)
7. [Post-Deployment](#post-deployment)
8. [Monitoring](#monitoring)
9. [Troubleshooting](#troubleshooting)

---

## Overview

This guide covers **production deployment** of SwX-API. For comprehensive deployment documentation, see the [Deployment Guide](docs/08-operations/DEPLOYMENT.md).

SwX-API supports multiple deployment options:
- **Docker Compose** - Recommended for most deployments
- **Cloud Platforms** - AWS, GCP, Azure, DigitalOcean
- **Kubernetes** - Container orchestration (advanced)

---

## Prerequisites

### Required

- **Docker** (20.10+) and **Docker Compose** (2.0+)
- **Domain name** (for production HTTPS)
- **DNS access** (to point domain to server)
- **Server** with minimum 2GB RAM, 2 CPU cores

### Recommended

- **SSL certificate** (automatically via Let's Encrypt with Caddy)
- **Monitoring tools** (Sentry, Prometheus, etc.)
- **Backup solution** (database backups)
- **CI/CD pipeline** (automated deployment)

---

## Deployment Options

### Option 1: Docker Compose (Recommended)

**Best for:** Most production deployments

**Configuration:**
- `docker-compose.production.yml`
- Caddy reverse proxy
- Automatic HTTPS via Let's Encrypt
- Production optimizations

**Deploy:**
```bash
# Set environment variables
export DOMAIN=api.yourdomain.com
export CADDY_EMAIL=admin@yourdomain.com

# Start services
docker compose -f docker-compose.production.yml up -d --build
```

### Option 2: Cloud Platform

**Best for:** Managed cloud deployments

**Supported Platforms:**
- **AWS** - ECS, EKS, EC2, App Runner
- **Google Cloud** - GKE, Cloud Run
- **Azure** - AKS, Container Instances
- **DigitalOcean** - App Platform, Droplets

**Deployment:**
- Use platform-specific deployment tools
- Adapt Docker Compose to platform format
- Configure platform-specific services (load balancers, databases, etc.)

### Option 3: Kubernetes

**Best for:** Large-scale, multi-region deployments

**Requirements:**
- Kubernetes cluster (1.20+)
- Helm (optional)
- Ingress controller
- Persistent volume support

**Deployment:**
- Convert Docker Compose to Kubernetes manifests
- Configure ingress for HTTPS
- Set up persistent volumes for database
- Configure secrets management

---

## Docker Deployment

### Production Docker Compose

**File:** `docker-compose.production.yml`

**Services:**
- `swx-api` - FastAPI application
- `postgres` - PostgreSQL database
- `redis` - Redis cache
- `caddy` - Reverse proxy and TLS termination

### Deployment Steps

**1. Clone Repository:**
```bash
git clone <repository-url>
cd swx-api-latest-backend
```

**2. Configure Environment:**
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with production values
nano .env
```

**3. Set Domain Variables:**
```bash
export DOMAIN=api.yourdomain.com
export CADDY_EMAIL=admin@yourdomain.com
```

**4. Start Services:**
```bash
# Build and start
docker compose -f docker-compose.production.yml up -d --build

# Check status
docker compose -f docker-compose.production.yml ps

# View logs
docker compose -f docker-compose.production.yml logs -f
```

**5. Verify Deployment:**
```bash
# Health check
curl https://api.yourdomain.com/api/utils/health-check

# API documentation
open https://api.yourdomain.com/docs
```

---

## Production Configuration

### Caddy Setup

Caddy automatically handles:
- **HTTPS** - Automatic SSL certificates via Let's Encrypt
- **HTTP to HTTPS** - Automatic redirect
- **Reverse Proxy** - Routes to API service
- **Security Headers** - Adds security headers

**Configuration:** `Caddyfile`

```caddy
api.yourdomain.com {
    reverse_proxy swx-api:8000
    header {
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        X-XSS-Protection "1; mode=block"
    }
}
```

### Database Configuration

**Production Database:**
- Use managed PostgreSQL (AWS RDS, Google Cloud SQL, etc.)
- Enable automated backups
- Configure connection pooling
- Set up read replicas for read-heavy workloads

**Connection String:**
```env
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname
```

### Redis Configuration

**Production Redis:**
- Use managed Redis (AWS ElastiCache, Google Cloud Memorystore, etc.)
- Enable persistence (RDB or AOF)
- Configure memory limits
- Set up replication for high availability

**Connection String:**
```env
REDIS_URL=redis://host:6379/0
```

---

## Environment Variables

### Required Variables

```env
# Application
ENVIRONMENT=production
SECRET_KEY=your-secret-key-here
ADMIN_SECRET_KEY=your-admin-secret-key-here

# Database
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname

# Redis
REDIS_URL=redis://host:6379/0
REDIS_PASSWORD=your-redis-password

# Domain
DOMAIN=api.yourdomain.com
CADDY_EMAIL=admin@yourdomain.com

# Admin User
FIRST_SUPERUSER=admin@example.com
FIRST_SUPERUSER_PASSWORD=secure-password
```

### Optional Variables

```env
# Email
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=user@example.com
SMTP_PASSWORD=password

# OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
FACEBOOK_CLIENT_ID=your-facebook-client-id
FACEBOOK_CLIENT_SECRET=your-facebook-client-secret

# Monitoring
SENTRY_DSN=your-sentry-dsn

# Stripe (for billing)
STRIPE_SECRET_KEY=your-stripe-secret-key
STRIPE_WEBHOOK_SECRET=your-stripe-webhook-secret
```

**⚠️ Security:** Never commit `.env` files. Use secrets management in production.

---

## Post-Deployment

### 1. Run Database Migrations

```bash
# Apply migrations
docker compose -f docker-compose.production.yml exec swx-api alembic upgrade head
```

### 2. Seed System Data

```bash
# Seed permissions, roles, plans, features
docker compose -f docker-compose.production.yml exec swx-api python scripts/seed_system.py
```

### 3. Verify Health

```bash
# Health check
curl https://api.yourdomain.com/api/utils/health-check

# Expected response:
# {
#   "status": "healthy",
#   "database": "connected",
#   "redis": "connected"
# }
```

### 4. Test Authentication

```bash
# Admin login
curl -X POST https://api.yourdomain.com/api/admin/auth/ \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=secure-password"
```

### 5. Run Acceptance Tests

```bash
# Run full user simulation
docker compose -f docker-compose.production.yml exec swx-api \
  python scripts/full_user_simulation.py
```

---

## Monitoring

### Health Checks

**Endpoint:** `/api/utils/health-check`

**Check:**
```bash
curl https://api.yourdomain.com/api/utils/health-check
```

### Application Logs

**View Logs:**
```bash
# All services
docker compose -f docker-compose.production.yml logs

# Specific service
docker compose -f docker-compose.production.yml logs swx-api

# Follow logs
docker compose -f docker-compose.production.yml logs -f swx-api
```

### Database Monitoring

**Check Database:**
```bash
# Connect to database
docker compose -f docker-compose.production.yml exec db psql -U ${DB_USER} -d ${DB_NAME}

# Check connections
SELECT * FROM pg_stat_activity;
```

### Redis Monitoring

**Check Redis:**
```bash
# Connect to Redis
docker compose -f docker-compose.production.yml exec redis redis-cli

# Check memory
INFO memory

# Check keys
KEYS *
```

---

## Troubleshooting

### Common Issues

**1. Service Won't Start**
```bash
# Check logs
docker compose -f docker-compose.production.yml logs swx-api

# Check status
docker compose -f docker-compose.production.yml ps
```

**2. Database Connection Failed**
```bash
# Check database status
docker compose -f docker-compose.production.yml ps db

# Test connection
docker compose -f docker-compose.production.yml exec db psql -U ${DB_USER} -d ${DB_NAME} -c "SELECT 1;"
```

**3. SSL Certificate Issues**
```bash
# Check Caddy logs
docker compose -f docker-compose.production.yml logs caddy

# Verify DNS
dig api.yourdomain.com
```

**4. Rate Limiting Issues**
```bash
# Check Redis
docker compose -f docker-compose.production.yml exec redis redis-cli ping

# Clear rate limits (if needed)
docker compose -f docker-compose.production.yml exec redis redis-cli FLUSHALL
```

### Getting Help

- **Documentation:** [docs/08-operations/DEPLOYMENT.md](docs/08-operations/DEPLOYMENT.md)
- **Troubleshooting:** [docs/10-troubleshooting/TROUBLESHOOTING.md](docs/10-troubleshooting/TROUBLESHOOTING.md)
- **FAQ:** [docs/10-troubleshooting/FAQ.md](docs/10-troubleshooting/FAQ.md)

---

## Next Steps

- Read [Operations Guide](docs/08-operations/OPERATIONS.md) for day-to-day operations
- Read [Monitoring Guide](docs/08-operations/MONITORING.md) for monitoring setup
- Read [Production Checklist](docs/08-operations/PRODUCTION_CHECKLIST.md) for production readiness
- Read [Security Best Practices](docs/05-security/SECURITY_BEST_PRACTICES.md) for security guidelines

---

**Status:** Deployment guide updated, ready for production use.
