# Container Inventory

**Date:** 2024  
**Status:** Phase 1 - Complete Inventory

---

## Executive Summary

This document provides a complete inventory of all containers defined across all Docker Compose files in the SwX-API stack.

**Total Containers Identified:** 5 unique services  
**Total Compose Files:** 4  
**Traefik Dependencies:** 3 services  
**Production Required:** 2 services

---

## Container Inventory Table

| Container Name | Purpose | Image | Ports | Dependencies | Healthcheck | Required in Production? | Notes |
|----------------|---------|-------|-------|--------------|-------------|------------------------|-------|
| **db** | PostgreSQL database with TimescaleDB | `timescale/timescaledb-ha:pg17` (base/override)<br>`postgres:15` (production) | Internal: 5432 | None | ✅ Yes<br>`pg_isready -U ${DB_USER} -d ${DB_NAME}` | ✅ **YES** | **CRITICAL:** Image inconsistency between base and production |
| **swx-api** | FastAPI application | Custom build from Dockerfile | Internal: 8000<br>Exposed: 8000 (dev) | db (healthy) | ⚠️ Yes (but endpoint may not exist)<br>`curl -f http://localhost:8000/api/utils/health-check` | ✅ **YES** | **CRITICAL:** Dockerfile references old `swx_api` path |
| **vectorizer-worker** | pgAI vectorizer worker for embeddings | `timescale/pgai-vectorizer-worker:v0.7.0` | None | db | ❌ **NO** | ❓ **UNKNOWN** | **SECURITY:** Hardcoded credentials in override file |
| **adminer** | Database admin UI | `adminer:latest` | Internal: 8080<br>Exposed: 8080 (dev) | db | ❌ **NO** | ❌ **NO** | Development tool only |
| **caddy** | Reverse proxy | `caddy:2-alpine` | 80, 443, 443/udp | swx-api | ✅ Yes<br>`caddy version` | ✅ **YES** | **REPLACES TRAEFIK** |

---

## Compose File Analysis

### 1. `docker-compose.yml` (Base/Production)

**Purpose:** Base configuration for production deployment

**Services:**
- `db` - TimescaleDB with pgAI support
- `vectorizer-worker` - AI vectorizer worker
- `adminer` - Database admin (with Traefik labels)
- `swx-api` - Main API (with Traefik labels)

**Networks:**
- `traefik-public` (external) - Requires pre-creation

**Volumes:**
- `app-db-data` - Database persistence

**Issues:**
- ❌ Depends on external `traefik-public` network
- ❌ Traefik labels on services
- ❌ No Traefik service defined (expects external)

---

### 2. `docker-compose.override.yml` (Development)

**Purpose:** Development overrides with hot reload

**Services:**
- `proxy` - Traefik for local development
- `db` - Same as base
- `vectorizer-worker` - **SECURITY ISSUE:** Hardcoded credentials
- `adminer` - Exposed on port 8080
- `swx-api` - Hot reload enabled, volume mounts

**Networks:**
- `traefik-public` (internal) - Created automatically
- `default` - Default network

**Volumes:**
- `app-db-data` - Database persistence
- Volume mounts for hot reload

**Issues:**
- ❌ Traefik service defined
- ❌ Hardcoded DB credentials in vectorizer-worker
- ❌ Old module path: `swx_api.core.main:app`
- ⚠️ Hot reload may not work with new structure

---

### 3. `docker-compose.production.yml` (Production)

**Purpose:** Production deployment with Traefik

**Services:**
- `traefik` - Reverse proxy with Let's Encrypt
- `db` - **INCONSISTENCY:** Uses `postgres:15` instead of TimescaleDB
- `adminer` - With Traefik labels
- `swx-api` - With Traefik labels

**Networks:**
- `traefik-public` (external) - Requires pre-creation

**Volumes:**
- `app-db-data` - Database persistence
- `traefik-public-certificates` - SSL certificates

**Issues:**
- ❌ **CRITICAL:** Database image mismatch (postgres:15 vs timescale/timescaledb-ha:pg17)
- ❌ Traefik service defined
- ❌ Missing `vectorizer-worker` (but base has it)
- ❌ Traefik dashboard exposed

---

### 4. `docker-compose.traefik.yml` (Traefik Standalone)

**Purpose:** Standalone Traefik setup

**Services:**
- `traefik` - Reverse proxy only

**Networks:**
- `traefik-public` (external) - Requires pre-creation

**Volumes:**
- `traefik-public-certificates` - SSL certificates

**Issues:**
- ❌ **TO BE DELETED** after Caddy migration

---

## Critical Issues Identified

### 🔴 CRITICAL: Database Image Inconsistency

**Issue:** Base compose uses `timescale/timescaledb-ha:pg17` but production uses `postgres:15`

**Impact:** Production may not have TimescaleDB or pgAI extensions

**Action Required:** Standardize on one image across all files

---

### 🔴 CRITICAL: Dockerfile References Old Structure

**Issue:** Dockerfile copies `swx_api` but codebase was refactored to `swx_core` and `swx_app`

**Lines:**
- Line 46: `COPY swx_api /app/swx_api`
- Line 65: `CMD ["/app/.venv/bin/uvicorn", "swx_api.core.main:app", ...]`

**Impact:** Container will not build or run correctly

**Action Required:** Update Dockerfile to new structure

---

### ✅ FIXED: Healthcheck Endpoint Created

**Issue:** Healthcheck tests `/api/utils/health-check` but this route did not exist

**Status:** ✅ **FIXED** - Created `swx_core/routes/utils/health_route.py` with:
- `GET /api/utils/health-check` - Basic health check for Docker
- `GET /api/utils/health` - Detailed health check with DB status

**Action Required:** None - Endpoint now exists

---

### 🟡 SECURITY: Hardcoded Credentials

**Issue:** `docker-compose.override.yml` has hardcoded DB credentials:
```yaml
PGAI_VECTORIZER_WORKER_DB_URL: postgres://czu_user:changeme@db:5432/czu_db
```

**Impact:** Credentials exposed in version control

**Action Required:** Use environment variables

---

### 🟡 WARNING: Missing Healthchecks

**Missing Healthchecks:**
- `vectorizer-worker` - No healthcheck defined
- `adminer` - No healthcheck defined
- `traefik` - No healthcheck defined

**Action Required:** Add healthchecks for all services

---

### 🟡 WARNING: Traefik Dependencies

**Services with Traefik labels:**
- `swx-api` - 11 Traefik labels
- `adminer` - 8 Traefik labels (base)
- `adminer` - 8 Traefik labels (production)

**Action Required:** Remove all Traefik labels after Caddy migration

---

## Network Analysis

### Networks Defined

| Network Name | Type | Scope | Used By |
|--------------|------|-------|---------|
| `traefik-public` | External | Global | All services (TO BE REMOVED) |
| `default` | Internal | Compose file | All services |

**Issues:**
- ❌ External network dependency
- ❌ Network name references Traefik

**Action Required:** Create new network for Caddy or use default

---

## Volume Analysis

### Volumes Defined

| Volume Name | Purpose | Persistent | Used By |
|-------------|---------|------------|---------|
| `app-db-data` | Database storage | ✅ Yes | db |
| `traefik-public-certificates` | SSL certificates | ✅ Yes | traefik (TO BE REMOVED) |

**Action Required:** Remove `traefik-public-certificates` after migration

---

## Production Readiness Assessment

### ✅ Production Ready
- `db` - Required, has healthcheck
- `swx-api` - Required, has healthcheck (but endpoint may not exist)

### ❌ Not Production Ready
- `vectorizer-worker` - No healthcheck, hardcoded credentials, unclear if needed
- `adminer` - Development tool, should not be in production
- `traefik` - To be replaced with Caddy

---

## Recommendations

### Immediate Actions

1. **Fix Dockerfile** - Update paths from `swx_api` to `swx_core`
2. **Standardize Database Image** - Choose one image (TimescaleDB or PostgreSQL)
3. **Verify Healthcheck Endpoint** - Create `/api/utils/health-check` or update healthcheck
4. **Remove Hardcoded Credentials** - Use environment variables
5. **Add Missing Healthchecks** - For all services

### Migration Actions

1. **Remove Traefik** - Delete all Traefik services and labels
2. **Add Caddy** - Single reverse proxy container
3. **Update Networks** - Remove `traefik-public`, use default or new network
4. **Remove Adminer from Production** - Development tool only
5. **Clarify vectorizer-worker** - Determine if needed in production

---

## Next Steps

1. ✅ **Phase 1 Complete** - Container inventory documented
2. ⏭️ **Phase 2** - Create smoke tests for each container
3. ⏭️ **Phase 3** - Add healthchecks
4. ⏭️ **Phase 4** - Migrate to Caddy
5. ⏭️ **Phase 5** - Final verification
