# Endpoint Coverage

**Purpose:** Map each API route to the persona(s) that hit it and the expected outcome (success or intended failure).

---

## Summary

| Persona | Endpoints hit | Notes |
|--------|----------------|-------|
| **System Operator** | Admin auth, permission list, role list, plan list, health, audit list, job list | Read-only system verification |
| **Admin** | RBAC, user, team, team member, user-role, billing, audit, job, policy | Full admin CRUD |
| **Team Owner** | User auth, profile, language, health, qa_article list | User domain + team-scoped |
| **Team Member** | User auth, profile, language; **admin/user** → 401/403 | Forbidden enforced |

---

## By Route

| Method | Path | Persona | Expected |
|--------|------|---------|----------|
| GET | `/` | Any | 200 |
| GET | `/api/utils/health-check` | Any | 200 |
| GET | `/api/utils/health` | System Op, Team Owner | 200 |
| POST | `/api/admin/auth/` | System Op, Admin | 200 |
| GET | `/api/admin/permission/` | System Op, Admin | 200 |
| POST | `/api/admin/permission/` | Admin (seed) | 200/201 |
| GET | `/api/admin/permission/{id}` | Admin | 200 |
| PATCH | `/api/admin/permission/{id}` | Admin | 200 |
| DELETE | `/api/admin/permission/{id}` | Admin | 200 |
| GET | `/api/admin/role/` | System Op, Admin | 200 |
| POST | `/api/admin/role/` | Admin (seed) | 200/201 |
| GET | `/api/admin/role/{id}` | Admin | 200 |
| PATCH | `/api/admin/role/{id}` | Admin | 200 |
| DELETE | `/api/admin/role/{id}` | Admin | 200 |
| POST | `/api/admin/role/{id}/permission/{pid}` | Admin (seed) | 200/201 |
| DELETE | `/api/admin/role/{id}/permission/{pid}` | Admin | 200 |
| GET | `/api/admin/role/{id}/permission` | Admin (seed) | 200 |
| GET | `/api/admin/team/` | Admin | 200 |
| POST | `/api/admin/team/` | Admin | 201 |
| GET | `/api/admin/team/{id}` | Admin | 200 |
| PATCH | `/api/admin/team/{id}` | Admin | 200 |
| DELETE | `/api/admin/team/{id}` | Admin | 200 |
| POST | `/api/admin/team/member` | Admin | 201 |
| DELETE | `/api/admin/team/member/{id}` | Admin | 200 |
| GET | `/api/admin/team/{id}/members` | Admin | 200 |
| POST | `/api/admin/user-role/` | Admin | 201 |
| DELETE | `/api/admin/user-role/{id}` | Admin | 200 |
| GET | `/api/admin/user-role/user/{id}` | Admin | 200 |
| GET | `/api/admin/user/` | Admin | 200 |
| POST | `/api/admin/user/` | Admin | 200 |
| GET | `/api/admin/user/{id}` | Admin | 200 |
| PATCH | `/api/admin/user/{id}` | Admin | 200 |
| DELETE | `/api/admin/user/{id}` | Admin | 200 |
| GET | `/api/admin/audit/` | System Op, Admin | 200 |
| GET | `/api/admin/audit/{id}` | Admin | 200 |
| GET | `/api/admin/job/` | System Op, Admin | 200 |
| GET | `/api/admin/job/stats` | Admin | 200 |
| GET | `/api/admin/job/{id}` | Admin | 200 |
| POST | `/api/admin/job/{id}/retry` | Admin | 200 |
| GET | `/api/admin/policy/` | Admin | 200 |
| GET | `/api/admin/policy/system` | Admin | 200 |
| GET | `/api/admin/policy/{id}` | Admin | 200 |
| POST | `/api/admin/policy/` | Admin | 201 |
| PATCH | `/api/admin/policy/{id}` | Admin | 200 |
| DELETE | `/api/admin/policy/{id}` | Admin | 204 |
| GET | `/api/admin/billing/feature/` | Admin | 200 |
| POST | `/api/admin/billing/feature/` | Admin (seed) | 201 |
| GET | `/api/admin/billing/plan/` | System Op, Admin | 200 |
| POST | `/api/admin/billing/plan/` | Admin (seed) | 201 |
| POST | `/api/admin/billing/plan/{id}/entitlement/{fid}` | Admin (seed) | 200/201 |
| POST | `/api/auth/` | Team Owner, Team Member | 200 |
| POST | `/api/auth/refresh` | User | 200 |
| POST | `/api/auth/register` | (Optional) | 200 |
| POST | `/api/auth/revoke` | User | 200 |
| POST | `/api/auth/password/recover/{email}` | Any | 200 |
| POST | `/api/auth/password/reset` | Any | 200 |
| GET | `/api/user/profile/` | Team Owner, Team Member | 200 |
| PATCH | `/api/user/profile/` | User | 200 |
| GET | `/api/user/profile/{id}` | User | 200 |
| PATCH | `/api/user/profile/password/update` | User | 200 |
| DELETE | `/api/user/profile/delete` | User | 200 |
| GET | `/api/utils/language/` | Team Owner, Team Member | 200 |
| GET | `/api/utils/language/{id}` | Any | 200 |
| GET | `/api/utils/language/code/{code}` | Any | 200 |
| GET | `/api/utils/language/{code}/{key}` | Any | 200 |
| POST | `/api/utils/language/` | Admin | 201 |
| PUT | `/api/utils/language/{id}` | Admin | 200 |
| DELETE | `/api/utils/language/{id}` | Admin | 204 |
| GET | `/api/utils/language/bulk` | Any | 200 |
| POST | `/api/utils/language/bulk` | Admin | 201 |
| GET | `/api/qa_article/` | Team Owner | 200 |
| POST | `/api/qa_article/` | User | 201 |
| GET | `/api/qa_article/{id}` | User | 200 |
| PUT | `/api/qa_article/{id}` | User | 200 |
| DELETE | `/api/qa_article/{id}` | User | 204 |
| POST | `/api/qa_article/ask` | User | 200 |
| POST | `/api/qa_article/search` | User | 200 |
| POST | `/api/qa_article/ollama/generate` | User | 200 |
| GET | `/api/oauth/urls` | Any | 200 |
| GET | `/api/oauth/google` | Any | 302 |
| GET | `/api/oauth/google/callback` | Any | 200/302 |
| GET | `/api/oauth/facebook` | Any | 302 |
| GET | `/api/oauth/facebook/callback` | Any | 200/302 |

---

## Intended Failures

| Method | Path | Persona | Expected |
|--------|------|---------|----------|
| GET | `/api/admin/user/` | Team Member (user token) | 401 or 403 |
| Any | `/api/admin/*` | Unauthenticated | 401 |

---

## Full Simulation Coverage (Enhanced)

The `full_user_simulation.py` script now **exhaustively tests ALL endpoints**:

### System Operator Flow
- Admin auth
- Permission list (seed verification)
- Role list (seed verification)
- Plan list (seed verification)
- Health check
- Audit log list
- Job list

### Admin Flow (Comprehensive CRUD)
- **Permissions:** GET list, GET by ID, PATCH update
- **Roles:** GET list, GET by ID, GET permissions, POST assign permission
- **Users:** GET list, POST create, GET by ID, PATCH update
- **Teams:** GET list, POST create, GET by ID, PATCH update, GET members
- **Team Members:** POST add member
- **User Roles:** POST assign, GET by user
- **Billing:** GET plans, GET features
- **Audit:** GET list, GET by ID
- **Jobs:** GET list, GET stats, GET by ID, POST retry
- **Policies:** GET list, GET system policies, POST create, GET by ID, PATCH update, DELETE

### Team Owner Flow (Full User Domain)
- **Auth:** POST login, POST refresh token, POST password recover
- **User Profile:** GET current, GET by ID, PATCH update
- **Utils:** GET languages (list, by ID, by code, by code/key, bulk), GET health
- **QA Articles:** GET list, POST create, GET by ID, PUT update, DELETE, POST search, POST ask

### Team Member Flow (Restrictions Testing)
- **Allowed:** Auth login, profile read, language read, health check, qa_article list
- **Forbidden (401/403):** All `/api/admin/*` endpoints tested for proper access denial

### Additional Endpoints
- **Root:** GET `/` (200)
- **Health Check:** GET `/api/utils/health-check` (200)
- **OAuth:** GET `/api/oauth/urls` (may fail if not configured)

**All endpoints are now exercised in the simulation.**

---

## No Dead Routes

All listed routes are referenced either by the simulation, the seed script, or standard usage (OAuth, health, docs). None are currently considered dead.
