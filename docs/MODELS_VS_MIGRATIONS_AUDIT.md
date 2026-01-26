# Models vs Migrations Audit

**Date:** 2026-01-25  
**Purpose:** Ensure all SQLModel tables and columns match the migration-defined schema.

---

## Tables and Sources

| Table | Model | Migration(s) |
|-------|-------|--------------|
| `language` | `Language` | a3b0fbc291c4 (init) |
| `refresh_token` | `RefreshToken` | a3b0fbc291c4 (init) |
| `user` → `users` | `User` | a3b0fbc291c4, 105a5ba553bd (rename + cols), 325a7c535a18 (drops those cols) |
| `qa_article` | `QaArticle` | cbd2b33666b6 |
| `permission` | `Permission` | add_rbac, 325 (drops created_at/updated_at, **drops UNIQUE(name)**) |
| `role` | `Role` | add_rbac, 325 (drops created_at/updated_at, **drops UNIQUE(name)**) |
| `role_permission` | `RolePermission` | add_rbac, 325 (drops **uq_role_permission**) |
| `team` | `Team` | add_rbac, 325 (drops created_at/updated_at) |
| `user_role` | `UserRole` | add_rbac, 325 (drops created_at/updated_at) |
| `team_member` | `TeamMember` | add_rbac, 325 (drops **uq_team_member**) |
| `admin_user` | `AdminUser` | add_rbac, 325 (**drops UNIQUE(email)**, **drops ix_admin_user_provider_id**) |
| `audit_log` | `AuditLog` | 325a7c535a18 |
| `billing_*` | `BillingAccount`, etc. | 8d6de0d76cce |
| `policy` | `Policy` | add_policy_table |
| `job` | `Job` | add_job_table |

**Note:** `qa_chunk` is created by pgai vectorizer (d10c894cceb1), not by our models. `QaChunk` has `table=False` and is schema-only.

---

## Mismatches Found

### 1. **Init migration – duplicate `UniqueConstraint('provider_id')`**

- **File:** `a3b0fbc291c4_init_table_for_all_the_core_model.py`
- **Issue:** `user` table has `sa.UniqueConstraint('provider_id')` twice (lines 59–60).
- **Fix:** Remove one. **Applied.**

### 2. **Migration 325 drops some uniques; models still expect them**

- **Issue:** 325’s upgrade drops:
  - `UNIQUE(admin_user.provider_id)` index (explicit `drop_index`)
  - `UNIQUE(role_id, permission_id)` on `role_permission`
  - `UNIQUE(team_id, user_id)` on `team_member`
  - Constraint unique on `permission.name`, `role.name`, `admin_user.email` (indexes `ix_permission_name`, `ix_role_name`, `ix_admin_user_email` from add_rbac are **not** dropped by 325, so those uniques remain).
- **Fix:** New migration `restore_uniques_001` after `add_job_table_001` restores:
  - `ix_admin_user_provider_id` (unique)
  - `uq_role_permission`
  - `uq_team_member`
  **Applied.**

### 3. **Job `last_error` type vs usage**

- **Model:** `last_error: Optional[str]` with `Column(JSONB)`.
- **Usage:** `job.last_error = {"error": ..., "attempt": ...}` or `None`.
- **Issue:** We store a dict; model types it as `str`.
- **Fix:** Change to `Optional[Dict[str, Any]]` and keep JSONB. **Applied.**

### 4. **105a5ba – raw SQL in `op.execute`**

- **Issue:** `op.execute("""UPDATE users SET identifier = email WHERE identifier IS NULL;""")` uses a raw string. Prefer `text()` for consistency.
- **Note:** Alembic accepts raw strings; `text()` is optional. Left as-is unless we touch this migration.

### 5. **Users `identifier` / `metadata` / `createdAt`**

- **Flow:** 105a5ba adds them; 325 **drops** them. Final schema matches `User` (no those columns).
- **Status:** OK.

---

## Summary of Fixes

| # | Item | Action |
|---|------|--------|
| 1 | Init duplicate `provider_id` unique | Removed duplicate in init migration |
| 2 | Uniques dropped by 325 | New migration restores them |
| 3 | Job `last_error` type | Model updated to `Dict[str, Any]` |
| 6 | Job runner jobstatus | Use `text("job.status = ANY(ARRAY['pending','queued']::jobstatus[])")` in `_acquire_job` |

---

### 6. **Job runner: jobstatus enum "PENDING" vs "pending"**

- **Issue:** Query used `Job.status == JobStatus.PENDING`; asyncpg sent `'PENDING'` (enum name). PostgreSQL `jobstatus` enum has lowercase values (`'pending'`, `'queued'`, …). Using `.value` / `.in_()` still resulted in enum-name binding via the ORM.
- **Fix:** Use a raw SQL fragment in `_acquire_job`: `text("job.status = ANY(ARRAY['pending','queued']::jobstatus[])")` so we send literal lowercase values. **Applied.**

---

## Verification

After fixes:

1. Run `alembic upgrade head` on a fresh DB.
2. Run `alembic check`.
3. Compare `alembic current` vs `alembic heads`.
4. Spot-check tables and constraints in DB (e.g. `\d users`, `\d permission`, etc.) vs models.
