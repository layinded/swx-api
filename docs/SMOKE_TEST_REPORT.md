# Smoke Test Report

**Date:** 2026-01-25  
**Suite:** `scripts/smoke_test.sh`  
**Compose:** `docker-compose.yml` only (no override).

---

## Configuration

- **COMPOSE_FILE:** `docker-compose.yml`
- **Pre-requisite:** Load `.env` (e.g. `set -a && . ./.env && set +a`) so `DB_USER` / `DB_NAME` match the db container for `pg_isready`.

---

## Tests Run

| # | Test | Result | Notes |
|---|------|--------|-------|
| 1 | Docker Compose available | ✅ | `docker compose` |
| 2 | Database (db) | ✅ | `pg_isready` |
| 3 | swx-api healthy | ✅ | Wait up to 60s |
| 4 | API health | ✅ | `GET /api/utils/health-check` → `"healthy"` |
| 5 | API root | ✅ | `GET /` → `"message"` |
| 6 | vectorizer-worker | ✅ | Container up |
| 7 | adminer | ✅ | Container up |
| 8 | Reverse proxy | ⚠️ | None (local dev); optional |

---

## Result

- **Total:** 7  
- **Passed:** 7  
- **Failed:** 0  
- **Verdict:** All critical tests passed.

---

## How to Run

```bash
(set -a && [ -f .env ] && . ./.env; set +a)
export COMPOSE_FILE=docker-compose.yml
./scripts/smoke_test.sh
```

---

## Other Smoke Scripts (Reference)

- `scripts/alert_smoke_test.sh` – Alerts  
- `scripts/billing_smoke_test.sh` – Billing  
- `scripts/user_simulation_smoke_test.sh` – User flows  
- `scripts/async_db_smoke_test.py` – Async DB  

The main gate uses `scripts/smoke_test.sh`; others can be run manually for extended validation.

---

## Repeatability (Phase 6)

**Second run from clean state:**

1. `./scripts/hard_reset.sh docker-compose.yml`
2. `docker compose -f docker-compose.yml up -d --build`
3. Wait for swx-api healthy (~50s), then `./scripts/smoke_test.sh`

**Result:** Smoke test passed on second full reset → boot → smoke run. Platform is release-ready from zero.
