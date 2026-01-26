# Settings Quick Reference: Database vs .env

**Quick decision guide for where to store settings.**

---

## Decision Tree

```
Is it a SECRET or CREDENTIAL?
├─ YES → .env (never database)
└─ NO → Continue...

Is it INFRASTRUCTURE/DEPLOYMENT specific?
├─ YES → .env (varies by environment)
└─ NO → Continue...

Is it needed at BUILD/STARTUP time?
├─ YES → .env (app won't start without it)
└─ NO → Continue...

Can USERS/ADMINS change it via UI/API?
├─ YES → Database (runtime config)
└─ NO → Continue...

Does it need to change WITHOUT REDEPLOYMENT?
├─ YES → Database (runtime config)
└─ NO → .env (or code default)
```

---

## Quick Lookup Table

| Setting | Location | Reason |
|---------|----------|--------|
| `SECRET_KEY` | ✅ .env | Secret, never expose |
| `DB_PASSWORD` | ✅ .env | Credential |
| `DB_HOST` | ✅ .env | Infrastructure |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | ⚠️ Database | User-configurable, security policy |
| `ENABLE_GOOGLE_LOGIN` | ⚠️ Database | Feature flag, runtime toggle |
| `EMAILS_FROM_EMAIL` | ⚠️ Database | Business config, marketing changes |
| `RATE_LIMIT_BURST` | ⚠️ Database | Business logic, frequent changes |
| `PROJECT_NAME` | ✅ .env | Build-time config |
| `LOG_LEVEL` | ✅ .env | Deployment-specific |
| `FRONTEND_HOST` | ✅ .env | Infrastructure (unless multi-tenant) |
| `GOOGLE_CLIENT_SECRET` | ✅ .env | OAuth secret |
| `AUDIT_RETENTION_DAYS` | ⚠️ Database | Compliance, runtime config |

---

## Examples

### ✅ Correct: Secrets in .env
```bash
# .env
SECRET_KEY=super-secret-key-123
DB_PASSWORD=my-secure-password
GOOGLE_CLIENT_SECRET=abc123xyz
```

### ✅ Correct: Infrastructure in .env
```bash
# .env
DB_HOST=db.example.com
REDIS_HOST=redis.example.com
ENVIRONMENT=production
```

### ⚠️ Should Move: Runtime Config to Database
```python
# Current: .env
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Recommended: Database
SystemConfig(
    key="auth.access_token_expire_minutes",
    value="10080",
    category="security"
)
```

### ⚠️ Should Move: Feature Flags to Database
```python
# Current: .env
ENABLE_GOOGLE_LOGIN=true

# Recommended: Database
FeatureFlag(
    key="enable_google_login",
    enabled=True,
    rollout_percentage=100
)
```

---

## Migration Checklist

When moving a setting from .env to database:

- [ ] Create database model/table
- [ ] Create service to read from DB (with .env fallback)
- [ ] Seed database with current .env value on first run
- [ ] Update code to use new service
- [ ] Create admin API endpoint (if user-configurable)
- [ ] Add audit logging for changes
- [ ] Update documentation
- [ ] Keep .env as fallback/default

---

## Anti-Patterns to Avoid

❌ **Don't store secrets in database**
- Passwords, API keys, tokens
- Even if encrypted, .env is safer

❌ **Don't store infrastructure in database**
- DB_HOST, REDIS_HOST (deployment-specific)
- ENVIRONMENT (varies by deployment)

❌ **Don't require database for app startup**
- Settings needed before DB connection should be .env
- Use database as enhancement, not requirement

✅ **Do use hybrid approach**
- Database for runtime config
- .env for secrets and infrastructure
- Code defaults as final fallback
