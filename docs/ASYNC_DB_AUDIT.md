# Async Database Audit

This document inventories and classifies database access points in the SwX-API codebase to ensure full async compliance.

## 1. Database Infrastructure

| Component | File | Status | Notes |
|-----------|------|--------|-------|
| Engine | `swx_core/database/db.py` | ❌ Sync | Uses `sqlalchemy.create_engine` |
| Session Factory | `swx_core/database/db.py` | ❌ Sync | Uses `sqlalchemy.orm.sessionmaker` with `Session` |
| Dependency | `swx_core/database/db.py` | ❌ Sync | `get_db` yields sync session |

## 2. Usage Classification

### ❌ Sync and Blocking (High Priority Refactor)
These must be converted to async to prevent event loop blocking.

| Category | Typical Usage | Files Affected |
|----------|---------------|----------------|
| Repositories | `session.exec(select(...))` | Most files in `swx_core/repositories/` and `swx_app/repositories/` |
| Auth Dependencies | `session.exec(statement).first()` | `swx_core/auth/admin/dependencies.py`, `swx_core/auth/user/dependencies.py` |
| Raw SQL | `db.execute(sql)` | `swx_app/repositories/qa_article_repository.py` (pgai/Ollama) |
| Health Check | `session.exec(text("SELECT 1"))` | `swx_core/routes/utils/health_route.py` |

### ⚠️ Sync but Isolated (Low Priority)
These are allowed to remain sync if they only run during startup or CLI operations.

| Category | File | Notes |
|----------|------|-------|
| Migrations | `migrations/env.py` | Alembic standard sync usage |
| Setup Script | `swx_core/database/db_setup.py` | Startup-only synchronization |
| Seed Script | `swx_core/database/db_seed.py` | Startup-only synchronization |

### ✅ Async-Safe
Already correctly using async patterns.

| Component | Usage |
|-----------|-------|
| OAuth Client | `httpx.AsyncClient()` in `swx_core/routes/access/oauth_route.py` |

## 3. Hidden Blocking Hotspots

| Issue | File/Location | Recommendation |
|-------|---------------|----------------|
| Password Hashing | `swx_core/security/password_security.py` | Move to `run_in_executor` or use async-native lib if possible |
| File I/O | `swx_core/utils/language_helper.py` | Cache translations in memory at startup |
| Email Sending | `swx_core/email/email_service.py` | Ensure `fastapi-mail` is used asynchronously |

## 4. Refactor Plan
- Replace `psycopg[binary]` with `asyncpg` in runtime.
- Switch to `sqlalchemy.ext.asyncio.create_async_engine`.
- Implement `AsyncSession` throughout the request lifecycle.
