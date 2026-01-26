# Personas for Production Acceptance

Four personas are used in the full user simulation. Each has separate credentials, tokens, and permissions.

---

## 1. System Operator

| Field | Value |
|-------|--------|
| **Identity** | Uses **admin** (superuser) credentials. Same as bootstrap superuser. |
| **Auth** | Admin domain: `POST /api/admin/auth/` |
| **Credentials** | `ADMIN_EMAIL` / `ADMIN_PASSWORD` (env). Default: `admin@example.com` / `changeme` (match `FIRST_SUPERUSER` / `FIRST_SUPERUSER_PASSWORD` in `.env`) |
| **Token** | Bearer JWT from admin login (audience `admin`) |
| **Capabilities** | Seed verification, global config read, audit log access, alert visibility (via logs/channels), job inspection |
| **Restrictions** | Must not act as normal user; cannot bypass policy engine |

**Flows:** System auth → seed verification → global config read → audit log access → job inspection.

---

## 2. Admin User

| Field | Value |
|-------|--------|
| **Identity** | Same as System Operator (admin superuser). |
| **Auth** | Admin domain: `POST /api/admin/auth/` |
| **Credentials** | Same as System Operator. |
| **Token** | Same Bearer JWT. |
| **Capabilities** | Create permissions, roles; assign permissions to roles; create users; assign admin roles; create plans; modify plan entitlements; view audit logs; trigger alerts (indirectly via actions). |
| **Restrictions** | All admin endpoints protected; no cross-domain access to user domain. |

**Flows:** Admin login → RBAC (permissions, roles, user-role assignments) → user CRUD → team CRUD → billing plans/features → audit logs.

---

## 3. Team Owner

| Field | Value |
|-------|--------|
| **Identity** | Normal user created via `POST /api/auth/register` or `POST /api/admin/user/`. |
| **Credentials** | `team_owner_*` (see simulation script). Example: `team_owner@example.com` / `TeamOwnerPass1!` |
| **Auth** | User domain: `POST /api/auth/` (form username=email, password) |
| **Token** | Bearer JWT from user login (audience `user`) |
| **Roles** | `team_owner` (user domain). Permissions: `user:read`, `team:read`, `team:write`, `team:manage`, `billing:read`, `billing:write`. |
| **Capabilities** | Create team, invite members, assign team roles, select billing plan, access paid features, hit rate limits, trigger background jobs. |
| **Restrictions** | Billing, policies, and rate limits enforced. |

**Flows:** User signup or admin-created user → login → create team → add members → assign roles → billing plan → rate limits → jobs.

---

## 4. Team Member (Normal)

| Field | Value |
|-------|--------|
| **Identity** | Normal user created via register or admin. |
| **Credentials** | `team_member_*`. Example: `team_member@example.com` / `MemberPass1!` |
| **Auth** | User domain: `POST /api/auth/` |
| **Token** | Bearer JWT (user). |
| **Roles** | `team_member`. Permissions: `user:read`, `team:read`. |
| **Capabilities** | Login, accept invite (role/team assignment), access allowed resources, attempt forbidden actions → policy denial. |
| **Restrictions** | Denials return correct errors; denials logged and audited. |

**Flows:** Login → access allowed resources → attempt forbidden actions → verify denials and audit.

---

## Credential Summary

| Persona | Email | Password | Domain |
|---------|--------|----------|--------|
| System Operator | `admin@example.com` | `changeme` (or env) | admin |
| Admin User | `admin@example.com` | `changeme` (or env) | admin |
| Team Owner | `team_owner@example.com` | `TeamOwnerPass1!` | user |
| Team Member | `team_member@example.com` | `MemberPass1!` | user |

Team Owner and Team Member are **created during the simulation** (via admin API or register). Their passwords are defined in the full simulation script.

---

## Token Usage

- **System Operator / Admin:** Use `access_token` from `POST /api/admin/auth/` in `Authorization: Bearer <token>` for all `/api/admin/*` requests.
- **Team Owner / Team Member:** Use `access_token` from `POST /api/auth/` in `Authorization: Bearer <token>` for `/api/user/*`, `/api/qa_article/*`, etc.

Refresh and revoke flows use `POST /api/auth/refresh` and `POST /api/auth/revoke` (user domain).
