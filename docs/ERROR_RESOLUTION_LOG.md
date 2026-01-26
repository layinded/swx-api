# Error Resolution Log

**Date:** 2026-01-25  
**Purpose:** Record all errors found during release gate and their fixes.

---

## 1. Prestart Permission Denied

- **Symptom:** `bash: /app/scripts/prestart.sh: Permission denied` when running prestart.  
- **Cause:** Script not executable in image; ran as `./prestart.sh` instead of `bash prestart.sh`.  
- **Fix:**  
  - `docker-compose.yml` and `docker-compose.production.yml`: use `bash /app/scripts/prestart.sh` (and production: `bash /app/...` then uvicorn).  
- **Files:** `docker-compose.yml`, `docker-compose.production.yml`.

---

## 2. `user_route`: `Depends` Not Defined

- **Symptom:** `NameError: name 'Depends' is not defined` in `swx_core.routes.user.user_route` (e.g. around `read_user_by_id`).  
- **Cause:** `Depends` used but not imported from FastAPI.  
- **Fix:** Add `Depends` to `from fastapi import ...` in `user_route.py`.  
- **Files:** `swx_core/routes/user/user_route.py`.

---

## 3. Redis `asyncio.run()` in Running Loop

- **Symptom:** `asyncio.run() cannot be called from a running event loop` when rate-limit middleware tested Redis at startup.  
- **Cause:** Startup Redis ping used `asyncio.run()` while uvicorn already had an event loop.  
- **Fix:** Remove startup Redis ping; log that client is configured and connection is verified on first use. Fail-closed behavior unchanged.  
- **Files:** `swx_core/middleware/rate_limit_middleware.py`.

---

## 4. Duplicate Table Registration (billing, policy)

- **Symptom:** `Table 'billing_account' is already defined for this MetaData instance` (and similar for `policy`).  
- **Cause:** `dynamic_import` reloads modules; model modules were reloaded and re-registered tables.  
- **Fix:** In `dynamic_import`, skip `importlib.reload` for any module whose full name contains `.models.`.  
- **Files:** `swx_core/utils/loader.py`.

---

## 5. Duplicate Migrations / `jobstatus` Already Exists

- **Symptom:** `type "jobstatus" already exists` during `alembic upgrade head`; migrations run twice (prestart + lifespan) and/or duplicate CREATE TYPE.  
- **Cause:**  
  - (a) Prestart and lifespan both ran `setup_database` → alembic.  
  - (b) `add_job_table` explicitly did `CREATE TYPE jobstatus` and also used `sa.Enum(..., name='jobstatus')` in `create_table`, which creates the type again.  
- **Fix:**  
  - (a) In `main.py` lifespan, when `DOCKERIZED=true`, skip `setup_database` and `seed_data`; prestart handles them.  
  - (b) In `add_job_table` migration, remove the explicit `CREATE TYPE jobstatus`; rely on `create_table`’s `sa.Enum` to create it.  
- **Files:** `swx_core/main.py`, `migrations/versions/add_job_table.py`.

---

## 6. Production Compose: API Exits After Prestart

- **Symptom:** Production `swx-api` ran only `bash scripts/prestart.sh`; container exited, no uvicorn.  
- **Cause:** Production override replaced command with prestart only.  
- **Fix:** Production command: run `bash /app/scripts/prestart.sh` then `exec` uvicorn (same pattern as base compose).  
- **Files:** `docker-compose.production.yml`.

---

## 7. Redundant `alembic upgrade head` in Prestart

- **Symptom:** Prestart ran both `db_setup` and `alembic upgrade head`; `db_setup` already runs alembic.  
- **Cause:** Prestart explicitly invoked alembic after `db_setup`.  
- **Fix:** Remove the extra `alembic upgrade head` from `prestart.sh`; keep only `python swx_core/database/db_setup.py`.  
- **Files:** `scripts/prestart.sh`.

---

## 8. Job Runner: Datetime Naive/Aware Mismatch

- **Symptom:** `invalid input for query argument $3: ... (can't subtract offset-naive and offset-aware datetimes)` in job runner `SELECT ... scheduled_at <= $3::TIMESTAMP WITHOUT TIME ZONE`.  
- **Cause:** Comparison used `datetime.now(timezone.utc)` (aware) while the bound parameter was treated as `TIMESTAMP WITHOUT TIME ZONE`.  
- **Fix:** Use `now_naive = datetime.now(timezone.utc).replace(tzinfo=None)` for the `scheduled_at <= now` comparison in `_acquire_job`.  
- **Files:** `swx_core/services/job/job_runner.py`.

---

## Summary

| # | Area            | Fix (short)                                              |
|---|-----------------|----------------------------------------------------------|
| 1 | Prestart        | Run via `bash /app/scripts/prestart.sh`                  |
| 2 | user_route      | Import `Depends` from FastAPI                            |
| 3 | Rate limit      | Remove Redis startup ping                                |
| 4 | Loader          | Skip reload for `.models.` modules                       |
| 5 | Migrations/bootstrap | DOCKERIZED skip setup_database; drop duplicate CREATE TYPE |
| 6 | Production      | Prestart + exec uvicorn                                  |
| 7 | Prestart        | Remove redundant `alembic upgrade head`                  |
| 8 | Job runner      | Use naive UTC for `scheduled_at` comparison              |

All changes applied; boot and smoke tests pass from a clean state.
