# State Integrity Report

**Purpose:** Document post-simulation state validation and consistency checks.

---

## 1. Database State

After `full_user_simulation.py` (with seed and all persona flows):

| Scope | Checks |
|-------|--------|
| **Tables** | All migrated tables exist; no extra tables from failed migrations. |
| **Referential integrity** | Foreign keys valid (user_id → users, role_id → role, team_id → team, etc.). |
| **Orphans** | No `user_role` without valid user/role; no `team_member` without valid team/user/role; no `role_permission` without valid role/permission. |
| **Enums** | `jobstatus`, `billingaccounttype`, `featuretype`, `subscriptionstatus`, `policyeffect` consistent with model definitions. |

---

## 2. Seed Idempotency

- **Permissions:** Keyed by `name`; re-run skips existing.
- **Roles:** Keyed by `name`; re-run skips existing.
- **Features:** Keyed by `key`; re-run skips existing.
- **Plans:** Keyed by `key`; re-run skips existing.
- **Plan entitlements:** Create duplicates avoided where unique (plan_id, feature_id) exists; seed handles “already exists” style responses.

Re-running `seed_system.py` must not duplicate data.

---

## 3. Audit Log Completeness

| Event | When | Expected |
|-------|------|----------|
| `admin.login` | Admin auth | Success and failure logged |
| `user.login` | User auth | Success and failure logged |
| `user.create` | Admin creates user | Logged |
| `team.create` | Admin creates team | Logged |
| `team.member.add` | Admin adds team member | Logged |
| `rate_limit.exceeded` | Rate limit hit | Logged when applicable |

Simulation verifies audit list endpoints return data (e.g. `GET /api/admin/audit/`). Fine-grained event checks can be added (e.g. filter by `action=user.create`).

---

## 4. Billing and Usage Consistency

- **Plans:** `free`, `pro`, `team`, `enterprise` present after seed.
- **Features:** `api.calls`, `llm.tokens`, `advanced.analytics`, `team.members` present.
- **Plan entitlements:** Free/Pro/Team/Enterprise limits as per `SEEDING_SPEC.md`.
- **Usage records:** Not created by the current simulation; no consistency check applied yet.

---

## 5. Validation Commands

Run after simulation (DB from compose):

```bash
# Connect to DB (compose)
docker compose -f docker-compose.yml exec -T db psql -U "${DB_USER:-postgres}" -d "${DB_NAME:-postgres}" -c "
SELECT 'user_role' AS tbl, COUNT(*) FROM user_role
UNION ALL SELECT 'team_member', COUNT(*) FROM team_member
UNION ALL SELECT 'role_permission', COUNT(*) FROM role_permission
UNION ALL SELECT 'audit_log', COUNT(*) FROM audit_log
UNION ALL SELECT 'billing_account', COUNT(*) FROM billing_account
UNION ALL SELECT 'job', COUNT(*) FROM job;
"
```

Manual checks:

- No broken FKs (e.g. `user_role.user_id` → `users.id`).
- `audit_log` has rows for admin login, user create, team create, team member add.

---

## 6. Post-Simulation State (Expected)

- **users:** Bootstrap superuser + 2 simulation users (team owner, team member).
- **admin_user:** Bootstrap admin.
- **role, permission, role_permission:** Seed data + any admin-created.
- **team, team_member:** At least one team and two members (owner, member).
- **user_role:** At least two assignments (owner, member).
- **audit_log:** Multiple entries (logins, creates, etc.).
- **job:** Zero or more (no jobs created by default simulation).
- **billing_***: Plans, features, entitlements from seed; accounts/subscriptions if/when billing flows are added.

---

## 7. Repeatability (Phase 6)

**Process:** Full environment reset → boot stack → run migrations (via prestart) → run full simulation.

1. On host: `./scripts/hard_reset.sh docker-compose.yml`
2. On host: `docker compose -f docker-compose.yml up -d --build`
3. Wait for API healthy (e.g. 55s)
4. Run simulation:  
   `docker compose exec -e API_URL=http://localhost:8000/api -e ADMIN_EMAIL=... -e ADMIN_PASSWORD=... -e RUN_PHASE0=0 swx-api python /app/scripts/full_user_simulation.py`

Repeat from step 1. **Both runs must pass.** Success criteria: seed completes, all persona flows pass, no unexpected errors.

---

## 8. Failure Handling

If state is inconsistent:

1. Fix the model, migration, or service logic that produced it.
2. Re-run Phase 0 (hard reset) → migrations → seed → full simulation.
3. Re-validate state and update this report if checks change.
