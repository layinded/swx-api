# Runtime Settings System - Implementation Complete

**Date:** 2026-01-26  
**Status:** ✅ IMPLEMENTED  
**Scope:** Runtime settings system with DB + .env fallback

---

## Executive Summary

A complete runtime settings system has been implemented that allows runtime-tunable configuration without redeployment, while maintaining security by keeping secrets in .env files.

**All phases completed successfully.**

---

## Phase 1: Settings Domain Design ✅

### SystemConfig Model

**File:** `swx_core/models/system_config.py`

**Features:**
- Type-safe value storage (int, bool, string, json)
- Category-based organization (security, rate_limit, feature_flag, email, jobs, policy, audit, general)
- Audit trail (updated_by, updated_at)
- Change history via `SystemConfigHistory` table
- Validation guards (no secrets, no invalid values)

**Migration:** `migrations/versions/add_system_config_tables.py`

---

## Phase 2: Settings Access Layer ✅

### Settings Service

**File:** `swx_core/services/settings_service.py`

**Features:**
- Priority: DB → .env → default
- Type-safe getters: `get_int()`, `get_bool()`, `get_string()`, `get_json()`
- In-memory caching with 60-second TTL
- Automatic cache invalidation on update
- Fail-closed for critical settings

**Helper Functions:** `swx_core/services/settings_helper.py`
- `get_token_expiration()` - Get token expiration timedeltas
- `get_feature_flag()` - Get feature flag values

---

## Phase 3: Admin Management API ✅

### Settings Routes

**File:** `swx_core/routes/admin/settings_route.py`

**Endpoints:**
- `GET /admin/settings/` - List all settings (filter by category)
- `GET /admin/settings/key/{key}` - Get setting by key
- `GET /admin/settings/{id}` - Get setting by ID
- `POST /admin/settings/` - Create new setting
- `PATCH /admin/settings/key/{key}` - Update setting
- `GET /admin/settings/key/{key}/history` - Get change history

**Features:**
- Admin-only access (RBAC enforced)
- All changes audit-logged
- Validation per value_type
- Security guards prevent secrets

---

## Phase 4: Migration of Existing Settings ✅

### Token Expiration Settings

**Migrated:**
- `ACCESS_TOKEN_EXPIRE_MINUTES` → `auth.access_token_expire_minutes` (DB)
- `REFRESH_TOKEN_EXPIRE_DAYS` → `auth.refresh_token_expire_days` (DB)
- `EMAIL_RESET_TOKEN_EXPIRE_HOURS` → `auth.email_reset_token_expire_hours` (DB)

**Updated Files:**
- `swx_core/services/auth_service.py` - Uses `get_token_expiration()`
- `swx_core/routes/admin/auth_route.py` - Uses `get_token_expiration()`
- `swx_core/security/password_security.py` - `generate_password_reset_token()` now async

**Fallback:** .env values used if DB setting not found

---

## Phase 5: Settings Seed Script ✅

### Seed Script

**File:** `scripts/seed_settings.py`

**Seeds:**
- Token expiration settings (from .env defaults)
- Feature flags (social login enable/disable)
- Email configuration (from address, from name)
- Audit log retention
- Job processing configs

**Integration:** Called automatically from `seed_system.py`

---

## Phase 6: Safety & Governance ✅

### Audit & Alert Integration

**Implemented:**
- All settings changes audit-logged via `get_audit_logger()`
- High-risk changes trigger alerts (token expiry, rate limits)
- Change history stored in `SystemConfigHistory` table

**High-Risk Settings:**
- `auth.access_token_expire_minutes`
- `auth.refresh_token_expire_days`
- `rate_limit.free.read.burst`
- `rate_limit.free.write.burst`

### Validation Guards

**File:** `swx_core/services/settings_crud_service.py`

**Guards:**
- ✅ Prevents secrets from being stored (keyword detection)
- ✅ Prevents invalid token expiration (must be positive, max 1 year)
- ✅ Prevents invalid rate limits (must be non-negative)
- ✅ Type validation (int, bool, string, json)

---

## Phase 7: Validation ✅

### Settings Smoke Test

**File:** `scripts/settings_smoke_test.py`

**Tests:**
- ✅ Settings load from DB
- ✅ Updates apply at runtime
- ✅ No redeploy required
- ✅ Cache invalidation works
- ✅ Audit logs created
- ✅ Validation guards working

---

## Usage Examples

### Reading Settings in Code

```python
from swx_core.services.settings_helper import get_token_expiration

# Get token expiration (DB -> .env -> default)
access_token_expires = await get_token_expiration(session, "access")
refresh_token_expires = await get_token_expiration(session, "refresh")
```

### Admin API Usage

```bash
# List all settings
GET /api/admin/settings/

# Get specific setting
GET /api/admin/settings/key/auth.access_token_expire_minutes

# Update setting (runtime, no redeploy)
PATCH /api/admin/settings/key/auth.access_token_expire_minutes
{
  "value": "10080"  # 7 days in minutes
}

# View change history
GET /api/admin/settings/key/auth.access_token_expire_minutes/history
```

---

## Settings Migrated to Database

| Setting Key | Category | Type | Default |
|-------------|----------|------|---------|
| `auth.access_token_expire_minutes` | security | int | 10080 (7 days) |
| `auth.refresh_token_expire_days` | security | int | 30 |
| `auth.email_reset_token_expire_hours` | security | int | 48 |
| `feature.enable_social_login` | feature_flag | bool | true |
| `feature.enable_google_login` | feature_flag | bool | true |
| `feature.enable_facebook_login` | feature_flag | bool | false |
| `feature.enable_github_login` | feature_flag | bool | false |
| `email.from_email` | email | string | (from .env) |
| `email.from_name` | email | string | "SwX API" |
| `audit.retention_days` | audit | int | 365 |
| `job.default_max_attempts` | jobs | int | 5 |
| `job.default_retry_delay_seconds` | jobs | int | 60 |
| `job.default_timeout_seconds` | jobs | int | 300 |

---

## Security Guarantees

✅ **No secrets in database** - Validation guards prevent secret keywords  
✅ **Type safety** - All values validated against declared type  
✅ **Audit trail** - Every change logged with history  
✅ **Alert integration** - High-risk changes trigger alerts  
✅ **Fail-closed** - Critical settings have safe defaults  

---

## Next Steps (Future Enhancements)

1. **Rate Limit Migration** - Move rate limit values from code to DB
2. **System Policies** - Migrate policy configurations to DB
3. **Multi-tenant Settings** - Per-organization settings support
4. **Settings UI** - Admin dashboard for settings management
5. **Settings API Documentation** - OpenAPI docs for settings endpoints

---

## Testing

### Run Settings Smoke Test

```bash
API_URL=http://localhost:8001/api \
  ADMIN_EMAIL=admin@example.com \
  ADMIN_PASSWORD=changeme \
  python scripts/settings_smoke_test.py
```

### Run Full Simulation (includes settings)

```bash
API_URL=http://localhost:8001/api \
  ADMIN_EMAIL=admin@example.com \
  ADMIN_PASSWORD=changeme \
  RUN_PHASE0=0 \
  python scripts/full_user_simulation.py
```

---

## Conclusion

✅ **Runtime settings system fully implemented**  
✅ **Token expiration migrated to DB**  
✅ **Admin API for settings management**  
✅ **Audit and alert integration**  
✅ **Validation guards in place**  
✅ **Smoke test validates functionality**  

The system now supports runtime configuration changes without redeployment while maintaining security by keeping secrets in .env files.
