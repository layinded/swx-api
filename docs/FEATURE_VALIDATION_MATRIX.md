# Feature Validation Matrix

**Date:** 2026-01-25  
**Scope:** Release gate – bootstrap, core services, and smoke test.

---

## Validation Summary

| Component | Validation | Status |
|-----------|------------|--------|
| **Boot** | Stack starts; prestart → migrations → uvicorn | ✅ |
| **DB** | Migrations apply; single head; tables exist | ✅ |
| **Redis** | Connected; rate-limit middleware configured | ✅ |
| **Auth** | Superuser created via db_setup; login/refresh not exercised in gate | 🔶 |
| **RBAC** | Tables present; role/permission routes registered | 🔶 |
| **Policy** | Tables present; policy routes registered | 🔶 |
| **Billing** | Tables present; billing routes registered | 🔶 |
| **Rate limiting** | Middleware applied; Redis client configured | ✅ |
| **Audit** | Tables present; audit middleware applied | ✅ |
| **Alerts** | Engine present; channels configured | 🔶 |
| **Jobs** | Job table + runner; handlers registered | ✅ |
| **Async DB** | Used by app; smoke test via API | ✅ |
| **Admin APIs** | Routes under `/api/admin/*` registered | ✅ |

🔶 = Structure and bootstrap verified; full E2E flows not run in this gate.

---

## Automated Checks (This Gate)

- **Phase 0:** Hard reset (containers, volumes, networks, caches).  
- **Phase 1:** Migration integrity (single head, linear chain); migrations apply on fresh DB.  
- **Phase 2:** Full stack boot; health + root endpoints.  
- **Phase 4:** `scripts/smoke_test.sh` – db, api health, api root, vectorizer, adminer.

---

## Manual / Follow-Up Validation

- Auth: login, refresh, logout.  
- RBAC: role CRUD, assignment, enforcement.  
- Policy: conditional access.  
- Billing: free / paid / team / expired.  
- Rate limiting: burst + sustained.  
- Audit: critical events logged.  
- Alerts: Slack/email/log routing.  
- Jobs: enqueue, retry, failure handling.  
- Async DB: concurrency safety.  
- Admin: access restricted.

Use `scripts/user_simulation_smoke_test.sh`, `scripts/billing_smoke_test.sh`, `scripts/alert_smoke_test.sh`, and `scripts/async_db_smoke_test.py` for deeper E2E checks.
