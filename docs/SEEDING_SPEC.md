# Seeding Specification

**Purpose:** Define what is seeded for production acceptance and user simulation. All seeding must be **idempotent** and executable via **API or official seed scripts** only. No manual SQL.

---

## 1. Bootstrap (Pre-Seed)

Done by `scripts/prestart.sh` → `swx_core/database/db_setup.py`:

| Item | Source | Idempotent |
|------|--------|------------|
| Alembic migrations | `alembic upgrade head` | Yes |
| User-domain superuser | `init_superuser` (User) | Yes – skip if exists |
| Admin-domain superuser | `init_superuser` (AdminUser) | Yes – skip if exists; password sync |
| Language translations | `seed_languages` from `languages.json` | Yes – skip (lang_code, key) if exists |

**Credentials:** `FIRST_SUPERUSER` / `FIRST_SUPERUSER_PASSWORD` (defaults: `admin@example.com` / `securepassword`).

---

## 2. System Seed (`scripts/seed_system.py`)

Runs **after** bootstrap. Uses **admin API** only (no direct DB writes). Idempotent: list-before-create; skip if already exists.

### 2.1 Core Permissions

| Name | Resource Type | Action | Description |
|------|---------------|--------|-------------|
| `user:read` | user | read | Read user profiles |
| `user:write` | user | write | Create/update users |
| `team:read` | team | read | Read teams |
| `team:write` | team | write | Create/update teams |
| `team:manage` | team | manage | Full team management |
| `billing:read` | billing | read | Read billing/plans |
| `billing:write` | billing | write | Manage subscriptions |
| `audit:read` | audit | read | Read audit logs |
| `job:read` | job | read | List/view jobs |
| `job:write` | job | write | Retry jobs |
| `policy:read` | policy | read | List/view policies |
| `policy:write` | policy | write | Create/update policies |

### 2.2 Core Features (Billing)

| Key | Type | Unit | Name |
|-----|------|------|------|
| `api.calls` | QUOTA | requests | API Calls |
| `llm.tokens` | QUOTA | tokens | LLM Tokens |
| `advanced.analytics` | BOOLEAN | – | Advanced Analytics |
| `team.members` | QUOTA | members | Team Members |

### 2.3 Default Plans

| Key | Name | Description |
|-----|------|-------------|
| `free` | Free Plan | Free tier |
| `pro` | Pro Plan | Pro tier |
| `team` | Team Plan | Team collaboration |
| `enterprise` | Enterprise Plan | Enterprise tier |

### 2.4 Plan Entitlements

- **Free:** `api.calls`=100, `llm.tokens`=1000, `advanced.analytics`=false  
- **Pro:** `api.calls`=10000, `llm.tokens`=100000, `advanced.analytics`=true  
- **Team:** `api.calls`=50000, `llm.tokens`=500000, `advanced.analytics`=true, `team.members`=50  
- **Enterprise:** higher quotas (e.g. 500000 / 5000000, etc.); `advanced.analytics`=true, `team.members`=500  

### 2.5 Default Rate Limit Configs

Defined in **code** (`swx_core/services/rate_limit/limit_registry.py`). Not stored in DB. Plans: `free`, `pro`, `team`, `enterprise`, `admin`, `system`, `anonymous`. No seeding required.

### 2.6 Default Policies

- **System policies:** Registered in code at startup (`register_system_policies()`), e.g. `team.update.owner`, `resource.update.own`, `superuser.bypass`.  
- **DB policies:** Optional; create via admin policy API if needed. Seed script may create **no** extra DB policies by default.

### 2.7 System Configuration

- **Env:** `FIRST_SUPERUSER`, `FIRST_SUPERUSER_PASSWORD`, `SECRET_KEY`, `REDIS_*`, `DB_*`, etc.  
- No DB-stored “system config” entity; configuration is env/settings only.

---

## 3. Idempotency Rules

- **Permissions:** List by name; create only if missing.  
- **Roles:** List by name; create only if missing.  
- **Features:** List by key; create only if missing.  
- **Plans:** List by key; create only if missing.  
- **Plan entitlements:** List by (plan_id, feature_id); create only if missing.  
- **Role–permission links:** Assign only if not already assigned.

Re-running `seed_system.py` must **not** duplicate data.

---

## 4. Execution Order

1. Bootstrap (migrations, superuser, languages) – via prestart.  
2. `seed_system.py`:  
   - Login as admin (`FIRST_SUPERUSER` / `FIRST_SUPERUSER_PASSWORD`).  
   - Seed permissions → roles → assign permissions to roles.  
   - Seed features → plans → plan entitlements.  
   - Optionally seed DB policies.

---

## 5. Usage

```bash
# From project root; API must be running.
export API_URL="${API_URL:-http://localhost:8001/api}"
export ADMIN_EMAIL="${ADMIN_EMAIL:-$FIRST_SUPERUSER}"
export ADMIN_PASSWORD="${ADMIN_PASSWORD:-$FIRST_SUPERUSER_PASSWORD}"
python scripts/seed_system.py
```

Script exits non‑zero on first unexpected error.
