# Deployment Guide

This document explains how to deploy SwX API using Docker Compose, Traefik, and CI/CD.

## 🌍 Requirements

- A cloud server with Docker installed
- A registered domain with a wildcard DNS entry (e.g., `*.swxapi.com`)
- TLS certificate (automatically handled by Traefik + Let's Encrypt)

## 🧰 Production Docker Compose

Use `docker-compose.production.yml` for a production deployment.

```bash
docker compose -f docker-compose.production.yml up -d --build
```

## 🌐 Traefik Setup

On your remote server:

```bash
docker network create traefik-public
export DOMAIN=swxapi.com
export EMAIL=admin@swxapi.com
export USERNAME=admin
export PASSWORD=yourpassword
export HASHED_PASSWORD=$(openssl passwd -apr1 $PASSWORD)
```

Then:

```bash
docker compose -f docker-compose.traefik.yml up -d
```

## 📁 Environment Variables

Define these securely in `.env` or as GitHub Secrets:

- `ENVIRONMENT=production`
- `DOMAIN=api.swxapi.com`
- `SECRET_KEY`
- `FIRST_SUPERUSER`, `FIRST_SUPERUSER_PASSWORD`
- `DATABASE_URL`
- `SENTRY_DSN` (optional)
