# Deployment Guide

**Version:** 1.0.0  
**Last Updated:** 2026-01-26

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Deployment Options](#deployment-options)
4. [Docker Deployment](#docker-deployment)
5. [Production Deployment](#production-deployment)
6. [Environment Configuration](#environment-configuration)
7. [Post-Deployment](#post-deployment)
8. [Rollback Procedures](#rollback-procedures)
9. [Troubleshooting](#troubleshooting)

---

## Overview

SwX-API supports **multiple deployment options** from local development to production. This guide covers deployment procedures, configuration, and best practices.

### Deployment Options

1. **Local Development** - Docker Compose for development
2. **Production** - Docker Compose with Caddy for HTTPS
3. **Cloud Platforms** - AWS, GCP, Azure, etc.
4. **Kubernetes** - Container orchestration (advanced)

---

## Prerequisites

### Required

- **Docker** (20.10+) and **Docker Compose** (2.0+)
- **Domain name** (for production HTTPS)
- **DNS access** (to point domain to server)
- **Server** with minimum 2GB RAM, 2 CPU cores

### Recommended

- **SSL certificate** (automatically via Let's Encrypt)
- **Monitoring tools** (Sentry, Prometheus, etc.)
- **Backup solution** (database backups)
- **CI/CD pipeline** (automated deployment)

---

## Deployment Options

### Option 1: Local Development

**Use Case:** Development and testing

**Configuration:**
- `docker-compose.yml` (default)
- Direct port exposure
- No HTTPS
- Development tools enabled

**Start:**
```bash
docker compose up -d
```

### Option 2: Production (Docker Compose)

**Use Case:** Production deployment with Docker Compose

**Configuration:**
- `docker-compose.production.yml`
- Caddy reverse proxy
- Automatic HTTPS
- Production optimizations

**Start:**
```bash
docker compose -f docker-compose.production.yml up -d --build
```

### Option 3: Cloud Platform

**Use Case:** Managed cloud deployment

**Platforms:**
- AWS (ECS, EKS, EC2)
- Google Cloud (GKE, Cloud Run)
- Azure (AKS, Container Instances)
- DigitalOcean (App Platform, Droplets)

**Deployment:**
- Use platform-specific deployment tools
- Adapt Docker Compose to platform format
- Configure platform-specific services

### Option 4: Kubernetes

**Use Case:** Large-scale, high-availability deployment

**Requirements:**
- Kubernetes cluster
- Helm charts (optional)
- Ingress controller
- Persistent volumes

**Deployment:**
- Convert Docker Compose to Kubernetes manifests
- Use Helm for configuration management
- Configure ingress for HTTPS

---

## Docker Deployment

### Development Deployment

**Step 1: Clone Repository**
```bash
git clone https://github.com/your-org/swx-api.git
cd swx-api
```

**Step 2: Configure Environment**
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
nano .env
```

**Step 3: Start Services**
```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Check status
docker compose ps
```

**Step 4: Verify Deployment**
```bash
# Check health
curl http://localhost:8001/api/utils/health-check

# Check API docs
open http://localhost:8001/docs
```

### Production Deployment

**Step 1: Prepare Server**
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

**Step 2: Configure Domain**
```bash
# Point domain to server IP
# A record: api.yourdomain.com -> YOUR_SERVER_IP
# A record: yourdomain.com -> YOUR_SERVER_IP
```

**Step 3: Configure Environment**
```bash
# Set environment variables
export DOMAIN=yourdomain.com
export CADDY_EMAIL=admin@yourdomain.com
export ENVIRONMENT=production

# Create .env file
cp .env.example .env
nano .env  # Configure all secrets
```

**Step 4: Deploy**
```bash
# Start production services
docker compose -f docker-compose.production.yml up -d --build

# Verify deployment
curl https://api.yourdomain.com/api/utils/health-check
```

---

## Production Deployment

### Production Configuration

**docker-compose.production.yml:**
- Caddy reverse proxy
- Automatic HTTPS via Let's Encrypt
- Security headers
- Production optimizations
- No development tools

**Caddy Configuration:**
- Automatic SSL certificate
- HTTP to HTTPS redirect
- Security headers
- Health check integration

### Deployment Steps

**1. Server Setup**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

**2. Application Setup**
```bash
# Clone repository
git clone https://github.com/your-org/swx-api.git
cd swx-api

# Configure environment
cp .env.example .env
nano .env  # Set all required variables
```

**3. DNS Configuration**
```bash
# Point domain to server
# A record: api.yourdomain.com -> YOUR_SERVER_IP
```

**4. Deploy**
```bash
# Set environment variables
export DOMAIN=yourdomain.com
export CADDY_EMAIL=admin@yourdomain.com

# Start services
docker compose -f docker-compose.production.yml up -d --build

# Monitor deployment
docker compose -f docker-compose.production.yml logs -f
```

**5. Verify**
```bash
# Check health
curl https://api.yourdomain.com/api/utils/health-check

# Check HTTPS
curl -I https://api.yourdomain.com/api/utils/health-check

# Check API docs
open https://api.yourdomain.com/docs
```

---

## Environment Configuration

### Required Environment Variables

**Application:**
```bash
ENVIRONMENT=production
DOMAIN=yourdomain.com
SECRET_KEY=your-secret-key-32-chars-minimum
REFRESH_SECRET_KEY=your-refresh-secret-key
PASSWORD_RESET_SECRET_KEY=your-reset-secret-key
```

**Database:**
```bash
DB_HOST=db
DB_PORT=5432
DB_NAME=swx_api
DB_USER=postgres
DB_PASSWORD=your-database-password
```

**Redis:**
```bash
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password  # Optional
REDIS_ENABLED=true
```

**Email:**
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-smtp-password
EMAILS_FROM_EMAIL=noreply@yourdomain.com
```

**Caddy:**
```bash
CADDY_EMAIL=admin@yourdomain.com  # For Let's Encrypt
```

### Optional Environment Variables

**Monitoring:**
```bash
SENTRY_DSN=your-sentry-dsn  # Error tracking
```

**OAuth:**
```bash
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
FACEBOOK_CLIENT_ID=your-facebook-client-id
FACEBOOK_CLIENT_SECRET=your-facebook-client-secret
```

**CORS:**
```bash
BACKEND_CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

---

## Post-Deployment

### Initial Setup

**1. Create Admin User**
```bash
# Via API
curl -X POST https://api.yourdomain.com/api/admin/auth \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@yourdomain.com",
    "password": "secure-password"
  }'

# Or via script
docker compose exec swx-api python scripts/reset_admin_password.py
```

**2. Seed System Data**
```bash
# Seed permissions, roles, plans, etc.
docker compose exec swx-api python scripts/seed_system.py
```

**3. Verify System**
```bash
# Run smoke tests
docker compose exec swx-api python scripts/smoke_test.sh

# Check all endpoints
curl https://api.yourdomain.com/api/utils/health
```

### Monitoring Setup

**1. Configure Sentry**
```bash
# Set SENTRY_DSN in .env
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
```

**2. Configure Alerting**
```bash
# Set Slack webhook
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

**3. Set Up Monitoring**
- Configure health check monitoring
- Set up log aggregation
- Configure alerting rules

---

## Rollback Procedures

### Application Rollback

**1. Stop Current Version**
```bash
docker compose -f docker-compose.production.yml down
```

**2. Checkout Previous Version**
```bash
git checkout <previous-commit-hash>
```

**3. Rebuild and Start**
```bash
docker compose -f docker-compose.production.yml up -d --build
```

**4. Verify Rollback**
```bash
curl https://api.yourdomain.com/api/utils/health-check
```

### Database Rollback

**1. Backup Current State**
```bash
docker compose exec db pg_dump -U ${DB_USER} ${DB_NAME} > backup-before-rollback.sql
```

**2. Restore Previous Backup**
```bash
docker compose exec -T db psql -U ${DB_USER} ${DB_NAME} < backup-previous.sql
```

**3. Run Migrations**
```bash
docker compose exec swx-api alembic downgrade -1
```

---

## Troubleshooting

### Common Deployment Issues

**1. "Port already in use"**
```bash
# Check what's using the port
sudo lsof -i :8001

# Stop conflicting service
sudo systemctl stop conflicting-service
```

**2. "Database connection failed"**
```bash
# Check database status
docker compose ps db

# Check database logs
docker compose logs db

# Test connection
docker compose exec db psql -U ${DB_USER} -d ${DB_NAME} -c "SELECT 1;"
```

**3. "Caddy certificate error"**
```bash
# Check DNS configuration
dig api.yourdomain.com

# Check Caddy logs
docker compose logs caddy

# Verify domain points to server
curl -I http://api.yourdomain.com
```

**4. "Service won't start"**
```bash
# Check logs
docker compose logs swx-api

# Check health
docker compose ps

# Check dependencies
docker compose ps db redis
```

### Debugging

**Enable Debug Logging:**
```bash
# Set debug log level
export LOG_LEVEL=DEBUG

# Restart service
docker compose restart swx-api

# View debug logs
docker compose logs -f swx-api
```

**Check Service Health:**
```bash
# Check all services
docker compose ps

# Check specific service
docker compose ps swx-api

# Check health endpoint
curl http://localhost:8001/api/utils/health
```

---

## Next Steps

- Read [Operations Guide](./OPERATIONS.md) for day-to-day operations
- Read [Monitoring Guide](./MONITORING.md) for monitoring setup
- Read [Production Checklist](./PRODUCTION_CHECKLIST.md) for production readiness

---

**Status:** Deployment guide documented, ready for implementation.
