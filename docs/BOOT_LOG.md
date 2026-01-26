# Boot Log – Full Stack Validation

**Date:** 2026-01-25  
**Scope:** Docker Compose stack (docker-compose.yml only, no override).

---

## Boot Sequence

1. **`docker compose -f docker-compose.yml up -d`**  
   - Starts: `db`, `redis`, `vectorizer-worker`, `adminer`, `swx-api`.

2. **DB & Redis**  
   - Healthchecks: `pg_isready` (db), `redis-cli ping` (redis).  
   - Both must be healthy before `swx-api` starts.

3. **swx-api**  
   - Command: `bash /app/scripts/prestart.sh` then `exec` uvicorn.  
   - **prestart:**  
     - `python swx_core/database/db_setup.py` → `check_db_ready` → `alembic upgrade head` → `init_superuser` → `seed_languages`.  
   - **uvicorn:** `swx_core.main:app` on `0.0.0.0:8000` with 4 workers.

4. **Lifespan (when not DOCKERIZED)**  
   - Runs `setup_database` and `seed_data`.  
   - With **DOCKERIZED=true**, lifespan skips these (prestart already did them).

---

## Verified Boot Output (Summary)

- **Prestart:** `Database setup complete!` after migrations and seeding.  
- **Alembic:** All migrations applied linearly through `add_job_table_001`.  
- **API:** Health check `GET /api/utils/health-check` → `{"status":"healthy","service":"swx-api"}`.  
- **Root:** `GET /` → `{"message":"Welcome to swX API 🚀"}`.

---

## Services Post-Boot

| Service           | Status    | Notes                                |
|-------------------|-----------|--------------------------------------|
| db                | healthy   | TimescaleDB, accepts connections     |
| redis             | healthy   | Redis 7 Alpine                       |
| swx-api           | healthy   | Port 8001→8000                       |
| vectorizer-worker | running   | pgai vectorizer                      |
| adminer           | healthy   | Dev DB UI                            |
| Reverse proxy     | —         | None (local dev); Caddy in prod      |

---

## Success Criteria

- [x] API boots and serves health + root.  
- [x] DB and Redis connect.  
- [x] Migrations apply during prestart.  
- [x] No unhandled startup errors; workers come up.
