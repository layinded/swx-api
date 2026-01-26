# Migration Audit & Environment Reset

**Date:** 2026-01-25  
**Purpose:** Release gate – full system validation, migration integrity, zero-error smoke test.

---

## Phase 0: Environment Reset (Exact Commands)

Hard reset must be **non-interactive** and **repeatable**. Use `scripts/hard_reset.sh`.

### Commands Used

```bash
# 1. Stop all containers, remove project volumes and networks
docker compose -f docker-compose.yml down -v --remove-orphans

# 2. Remove orphan networks (not used by any container)
docker network prune -f

# 3. Remove dangling images
docker image prune -f

# 4. Remove unused (orphan) volumes
docker volume prune -f

# 5. Clear Python caches (project root)
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true
```

### Script

- **`scripts/hard_reset.sh`** – Wraps the above. Usage: `./scripts/hard_reset.sh [COMPOSE_FILES]`
- Default: `docker-compose.yml` only (no override) for release gate.

---

## Phase 1: Migration Integrity Check

### Revision Graph

- **Heads:** exactly **one** → `restore_uniques_001`
- **Orphan revisions:** none
- **Missing dependencies:** none
- **Branches:** none (linear chain)

### Linear Chain (oldest → newest)

| Revision | Description |
|----------|-------------|
| `a3b0fbc291c4` | Init table for all the core model |
| `7997f79106f4` | Add pgai and pgvector extensions |
| `cbd2b33666b6` | Migration for model QaArticle |
| `d10c894cceb1` | Migration for model create pgAI vectorizer for qa_article |
| `105a5ba553bd` | Rename user table to users and add Chainlit fields |
| `add_rbac_admin_user` | Add RBAC tables and admin_user table |
| `325a7c535a18` | Add audit_log table |
| `8d6de0d76cce` | Add billing tables |
| `add_policy_table_001` | Add policy table |
| `add_job_table_001` | Add job table |
| `restore_uniques_001` | Restore unique constraints dropped by 325 **(head)** |

### Validation Commands

```bash
docker run --rm -e DB_HOST=localhost -e DB_NAME=postgres -e DB_USER=postgres -e DB_PASSWORD=postgres -w /app swx-api:latest alembic heads
# Expected: restore_uniques_001 (head)

docker run --rm -e DB_HOST=localhost -e DB_NAME=postgres -e DB_USER=postgres -e DB_PASSWORD=postgres -w /app swx-api:latest alembic history -v
# Expected: single linear chain, one head
```

### Schema vs Models

- Migrations define schema; `swx_core` / `swx_app` models are loaded via `swx_core.utils.model.load_all_models()` in `migrations/env.py`.
- Target metadata: `SQLModel.metadata`. Base model: `swx_core.models.base.Base` (extends SQLModel).

### Fixes Applied (Release Gate)

1. **`scripts/prestart.sh`**  
   - Removed redundant `alembic upgrade head` (already run inside `db_setup.py`).

2. **`docker-compose.production.yml`**  
   - `swx-api` command changed from only `bash scripts/prestart.sh` to:
     - Run `bash /app/scripts/prestart.sh` then `exec` uvicorn.  
   - Ensures DB setup + migrations run, then the API process stays up.

3. **`migrations/versions/add_job_table.py`**  
   - Removed explicit `CREATE TYPE jobstatus`; it was duplicated when `op.create_table(..., sa.Enum(..., name='jobstatus'), ...)` also creates the type. Rely on the column’s `sa.Enum` only.

---

## Phase 1 (continued): Migration Execution

Migrations are applied during **application boot** via:

1. `scripts/prestart.sh` → `python swx_core/database/db_setup.py`
2. `db_setup.setup_database()` → `check_db_ready()` → `run_alembic_migrations()` (i.e. `alembic upgrade head`) → `init_superuser()` → `seed_languages()`

No manual migration steps are required for a clean boot.

---

## Success Criteria (Migrations)

- [x] Exactly one Alembic head
- [x] Linear revision graph, no orphans
- [x] Migrations apply during stack boot (prestart → db_setup → alembic)
- [x] No manual DB edits; schema aligned with models
