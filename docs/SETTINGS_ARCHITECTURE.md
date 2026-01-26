# Settings Architecture: Database vs .env Recommendations

**Purpose:** Define which settings belong in `.env` (environment/config) vs database (runtime configuration).

---

## Principles

### **Keep in .env** (Environment/Config Files)
- **Secrets & Credentials** - Never commit, never expose via API
- **Infrastructure Settings** - Deployment-specific, varies by environment
- **Build-time Configuration** - Needed before app starts
- **Security-sensitive** - Tokens, keys, passwords
- **Environment-specific** - Dev/staging/prod differences
- **Third-party Service Credentials** - External API keys

### **Keep in Database** (Runtime Configuration)
- **User-configurable Settings** - Admins/users can change via UI/API
- **Business Logic Settings** - Settings that affect application behavior
- **Multi-tenant Settings** - Per-organization/team configurations
- **Feature Toggles** - Runtime feature enable/disable
- **Application Preferences** - User preferences, UI settings
- **Settings Requiring No Redeployment** - Changes without restart
- **Auditable Changes** - Settings that need audit logs

---

## Current Settings Analysis

### ✅ **Correctly in .env** (Keep as-is)

#### **Security & Secrets**
- `SECRET_KEY` - JWT signing key
- `REFRESH_SECRET_KEY` - Refresh token signing
- `PASSWORD_RESET_SECRET_KEY` - Password reset tokens
- `DB_PASSWORD` - Database password
- `REDIS_PASSWORD` - Redis password
- `SMTP_PASSWORD` - Email service password
- `GOOGLE_CLIENT_SECRET` - OAuth secrets
- `FACEBOOK_CLIENT_SECRET` - OAuth secrets
- `SENTRY_DSN` - Error tracking (contains token)

#### **Infrastructure & Deployment**
- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_NAME` - Database connection
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB` - Redis connection
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER` - Email service
- `BACKEND_HOST`, `FRONTEND_HOST` - Service URLs
- `DOCKERIZED` - Environment detection
- `ENVIRONMENT` - Deployment environment (local/staging/production)

#### **Build-time Configuration**
- `PROJECT_NAME` - Application name
- `ROUTE_PREFIX` - API route prefix
- `API_VERSIONS` - Supported API versions
- `DEFAULT_API_VERSION` - Default version
- `LOG_LEVEL` - Logging verbosity
- `BACKEND_CORS_ORIGINS` - CORS configuration

#### **Third-party Credentials**
- `GOOGLE_CLIENT_ID`, `GOOGLE_AUTH_URL`, `GOOGLE_REDIRECT_URI`
- `FACEBOOK_CLIENT_ID`, `FACEBOOK_AUTH_URL`, `FACEBOOK_REDIRECT_URI`
- `OLLAMA_HOST` - LLM service URL

#### **Bootstrap Settings**
- `FIRST_SUPERUSER` - Initial admin email
- `FIRST_SUPERUSER_PASSWORD` - Initial admin password

---

## Recommended: Move to Database

### **1. Token Expiration Settings** ⚠️

**Current:** `.env`
```python
ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
REFRESH_TOKEN_EXPIRE_DAYS: int = 30
EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48
```

**Recommendation:** **Database** (with .env defaults)

**Why:**
- Security teams may need to adjust token lifetimes without redeployment
- Compliance requirements may change
- Different expiration for different user roles/plans
- Audit trail needed for security policy changes

**Implementation:**
```python
# .env (defaults)
ACCESS_TOKEN_EXPIRE_MINUTES=10080  # 7 days default

# Database (SystemConfig table)
{
  "key": "auth.access_token_expire_minutes",
  "value": "10080",
  "description": "Access token expiration in minutes",
  "category": "security",
  "is_public": false,
  "updated_by": "admin@example.com",
  "updated_at": "2026-01-26T..."
}
```

---

### **2. Rate Limit Configuration** ⚠️

**Current:** Code (`swx_core/services/rate_limit/limit_registry.py`)

**Recommendation:** **Database** (with code defaults)

**Why:**
- Business needs change rate limits frequently
- Different limits per plan (already in DB via plans, but limits hardcoded)
- A/B testing different rate limit strategies
- No redeployment needed for limit adjustments

**Implementation:**
```python
# Database: rate_limit_config table
{
  "plan_key": "free",
  "feature": "api_requests",
  "endpoint_class": "read",
  "limit_type": "burst",
  "value": 10000,
  "updated_at": "..."
}
```

**Fallback:** Code defaults if DB config missing

---

### **3. Email Configuration (Non-secret parts)** ⚠️

**Current:** `.env`
```python
EMAILS_FROM_EMAIL: str | None = None
EMAILS_FROM_NAME: str | None = None
SMTP_TLS: bool = True
SMTP_SSL: bool = False
```

**Recommendation:** **Hybrid**
- **Keep in .env:** `SMTP_HOST`, `SMTP_PASSWORD`, `SMTP_USER` (secrets)
- **Move to DB:** `EMAILS_FROM_EMAIL`, `EMAILS_FROM_NAME` (business config)
- **Keep in .env:** `SMTP_TLS`, `SMTP_SSL` (infrastructure config)

**Why:**
- Marketing may want to change "from" name/email
- Multi-brand support (different from addresses)
- No redeployment needed

---

### **3b. Social Login Enable/Disable Flags** ⚠️

**Current:** `.env`
```python
ENABLE_SOCIAL_LOGIN: bool = True
ENABLE_GOOGLE_LOGIN: bool = True
ENABLE_FACEBOOK_LOGIN: bool = False
ENABLE_GITHUB_LOGIN: bool = False
```

**Recommendation:** **Database** (with .env defaults)

**Why:**
- Enable/disable OAuth providers without redeployment
- A/B testing different auth methods
- Emergency disable if OAuth provider has issues
- Feature flag pattern

**Keep in .env:**
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` (credentials)
- `FACEBOOK_CLIENT_ID`, `FACEBOOK_CLIENT_SECRET` (credentials)
- OAuth URLs and redirect URIs (infrastructure)

---

### **4. Feature Flags** ⚠️

**Current:** Not implemented

**Recommendation:** **Database**

**Why:**
- Enable/disable features without code deployment
- Gradual rollouts (percentage-based)
- A/B testing
- Emergency feature disable

**Implementation:**
```python
# Database: feature_flag table
{
  "key": "enable_advanced_analytics",
  "enabled": true,
  "rollout_percentage": 100,
  "description": "Enable advanced analytics dashboard",
  "updated_at": "..."
}
```

---

### **5. Application-wide Settings** ⚠️

**Current:** `.env`
```python
PROJECT_NAME: str
FRONTEND_HOST: str
```

**Recommendation:** **Hybrid**
- **Keep in .env:** `PROJECT_NAME` (build-time)
- **Move to DB:** `FRONTEND_HOST` (if multi-tenant, per-org frontends)

**Why:**
- Multi-tenant apps may have different frontend URLs per organization
- White-label support

---

### **6. System Policies (Default Policies)** ⚠️

**Current:** Code (`register_system_policies()`)

**Recommendation:** **Database** (with code defaults)

**Why:**
- Admins need to modify policies without code changes
- Policy tuning based on usage patterns
- Compliance requirements change

**Implementation:**
- System policies seeded from code on first run
- Admins can modify via API
- Code provides defaults if DB empty

---

### **7. Audit Log Retention** ⚠️

**Current:** Not configured

**Recommendation:** **Database**

**Why:**
- Compliance requirements vary
- Storage costs may require adjustment
- Retention policies change over time

**Implementation:**
```python
# Database: system_config
{
  "key": "audit.retention_days",
  "value": "365",
  "description": "Audit log retention in days"
}
```

---

### **8. Job Processing Settings** ⚠️

**Current:** Code/hardcoded

**Recommendation:** **Database**

**Why:**
- Adjust job retry limits based on load
- Change job priority strategies
- Configure job timeouts per environment

**Implementation:**
```python
# Database: job_config
{
  "job_type": "billing_sync",
  "max_attempts": 5,
  "retry_delay_seconds": 60,
  "timeout_seconds": 300
}
```

---

## Recommended: Keep in .env (Current is Correct)

### ✅ **Security Settings**
- All secret keys, passwords, tokens
- OAuth client secrets
- Database credentials
- Redis credentials
- SMTP credentials

### ✅ **Infrastructure**
- Database connection strings
- Redis connection
- Service URLs (backend, frontend)
- Docker detection
- Environment type

### ✅ **Build-time Config**
- API route prefixes
- API versions
- Log levels
- CORS origins (deployment-specific)

---

## Implementation Strategy

### **Phase 1: Create SystemConfig Model**

```python
# swx_core/models/system_config.py
class SystemConfig(Base, table=True):
    key: str = Field(unique=True, index=True)
    value: str  # JSON-encoded for complex types
    description: str | None
    category: str  # "security", "feature", "rate_limit", etc.
    is_public: bool = False  # Can non-admins read?
    updated_by: str | None  # Admin email
    updated_at: datetime
```

### **Phase 2: Settings Service**

```python
# swx_core/services/settings_service.py
class SettingsService:
    async def get_setting(key: str, default: Any = None) -> Any:
        """Get setting from DB, fallback to .env/default"""
        
    async def set_setting(key: str, value: Any, updated_by: str):
        """Update setting in DB with audit"""
```

### **Phase 3: Migration Path**

1. **Read from DB first, fallback to .env**
2. **Seed DB with .env values on first run**
3. **Admin API to manage settings**
4. **Audit all setting changes**

---

## Settings Priority Order

When reading settings, use this priority:

1. **Database** (runtime config) - Highest priority for user-configurable
2. **Environment variables** (`.env`) - For secrets and infrastructure
3. **Code defaults** - Fallback for missing values

```python
def get_setting(key: str) -> Any:
    # 1. Try database
    db_value = await db.get_system_config(key)
    if db_value:
        return db_value
    
    # 2. Try environment
    env_value = os.getenv(key)
    if env_value:
        return env_value
    
    # 3. Use code default
    return DEFAULT_VALUES[key]
```

---

## Security Considerations

### **Never Store in Database:**
- ❌ Passwords (hashed only)
- ❌ Secret keys (JWT signing keys)
- ❌ API keys/tokens
- ❌ Database credentials
- ❌ OAuth client secrets

### **Safe to Store in Database:**
- ✅ Token expiration times (not the keys)
- ✅ Rate limit values (not Redis passwords)
- ✅ Feature flags (boolean/string)
- ✅ UI preferences
- ✅ Business logic settings

---

## Summary Table

| Setting Category | Current Location | Recommended | Priority |
|-----------------|------------------|-------------|----------|
| **Secrets/Passwords** | .env | ✅ .env | Keep |
| **Infrastructure URLs** | .env | ✅ .env | Keep |
| **Token Expiration** | .env | ⚠️ Database | Move |
| **Rate Limits** | Code | ⚠️ Database | Move |
| **Feature Flags** | None | ⚠️ Database | Add |
| **Email From Address** | .env | ⚠️ Database | Move |
| **Social Login Flags** | .env | ⚠️ Database | Move |
| **System Policies** | Code | ⚠️ Database | Move |
| **Audit Retention** | None | ⚠️ Database | Add |
| **Job Config** | Code | ⚠️ Database | Move |
| **CORS Origins** | .env | ✅ .env | Keep |
| **Log Level** | .env | ✅ .env | Keep |

---

## Quick Reference

### **Always .env:**
- `SECRET_KEY`, `*_SECRET_KEY`
- `*_PASSWORD`
- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_NAME`
- `REDIS_HOST`, `REDIS_PORT`
- `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`
- `ENVIRONMENT`, `DOCKERIZED`
- `BACKEND_HOST`, `FRONTEND_HOST`
- `LOG_LEVEL`

### **Should be Database:**
- Token expiration times
- Rate limit values
- Feature flags
- Email from name/address (non-secret)
- Social login enable/disable flags
- System policy configurations
- Audit log retention
- Job processing configs
- User-configurable business settings

---

## Next Steps

1. **Create `SystemConfig` model** for runtime settings
2. **Create settings service** with DB + .env fallback
3. **Migrate token expiration** settings first (low risk)
4. **Migrate rate limits** (already partially in DB via plans)
5. **Add feature flags** system
6. **Create admin API** for settings management
7. **Add audit logging** for all setting changes
