# Architecture Audit Report

**Date:** 2024  
**Auditor:** Staff-level Backend Architect  
**Scope:** Full codebase audit for framework refactoring

---

## Executive Summary

This codebase is a FastAPI application with mixed concerns: framework-level infrastructure and application-specific business logic. The architecture needs significant refactoring to separate reusable framework code from application-specific implementations.

**Critical Issues:**
- No clear separation between framework and application code
- Chainlit integration pollutes core models
- RBAC is non-existent (only boolean `is_superuser` flag)
- Admin and user domains are not isolated
- No team/tenant isolation
- Dynamic route loading creates implicit coupling

---

## Module Analysis

### 1. Core Framework Modules (`swx_api/core/`)

#### ✅ Framework-Level (Should Stay)
- `core/config/` - Settings management (framework)
- `core/database/` - Database connection and setup (framework)
- `core/middleware/` - CORS, logging, Sentry (framework)
- `core/utils/` - Helper utilities (framework)
- `core/cli/` - CLI scaffolding (framework, but needs hardening)

#### ⚠️ Mixed Concerns (Needs Refactoring)
- `core/models/` - Contains both framework models (User, Token) and app-specific (Language)
  - **Issue:** User model has Chainlit-specific fields (`identifier`, `user_metadata`)
  - **Issue:** No RBAC models (Permission, Role, etc.)
  - **Action:** Split into framework models and example models

- `core/security/` - Auth logic mixed with user management
  - **Issue:** Single `get_current_user` handles all auth
  - **Issue:** No separation between admin and user auth
  - **Action:** Split into `auth/core`, `auth/admin`, `auth/user`

- `core/routes/` - Routes mixed with business logic
  - **Issue:** Admin routes use same User model as user routes
  - **Issue:** No clear domain boundaries
  - **Action:** Separate admin and user route handlers

- `core/services/` - Business logic mixed with framework services
  - **Issue:** `auth_service.py` handles both admin and user flows
  - **Action:** Split into domain-specific services

- `core/repositories/` - Data access layer
  - **Status:** Generally framework-level, but needs permission checks

- `core/controllers/` - Request handling
  - **Status:** Framework-level pattern, but needs domain separation

#### ❌ Application-Specific (Should Move to Example)
- `core/models/language.py` - Translation system (app-specific)
- `core/database/languages.json` - Translation data (app-specific)
- `core/services/language_service.py` - Language business logic (app-specific)
- `core/repositories/language_repository.py` - Language data access (app-specific)
- `core/controllers/language_controller.py` - Language endpoints (app-specific)
- `core/routes/utils/` - Utility routes (likely app-specific)

---

### 2. Application Modules (`swx_api/app/`)

#### Status: Application-Specific (Should Move to Example)
All modules under `swx_api/app/` are application-specific:
- `app/models/qa_article.py`, `qa_chunk.py` - Business domain models
- `app/controllers/qa_article_controller.py` - Business logic
- `app/services/qa_article_service.py` - Business services
- `app/repositories/qa_article_repository.py` - Data access
- `app/routes/qa_article_route.py` - API endpoints

**Action:** Move to `swx_app/` as demonstration code.

---

### 3. Scripts (`scripts/`)

#### ❌ Must Delete
- `scripts/chainlit_app.py` - Chainlit demo application
  - **Issue:** Hardcoded API URLs
  - **Issue:** LLM integration code
  - **Action:** DELETE

#### ✅ Framework-Level (Should Stay)
- `scripts/format.sh` - Code formatting
- `scripts/lint.sh` - Linting
- `scripts/test.sh` - Testing
- `scripts/prestart.sh` - Pre-startup checks

---

### 4. CLI (`swx_api/core/cli/`)

#### ⚠️ Needs Hardening
- `cli/commands/make.py` - Resource scaffolding
  - **Issue:** No security validation
  - **Issue:** Allows any module path
  - **Issue:** No pattern enforcement
  - **Action:** Add validation, enforce naming conventions, prevent insecure patterns

- `cli/commands/resource_templates.py` - Code generation templates
  - **Status:** Framework-level, but templates need security review

---

## Dependency Analysis

### Circular Dependencies

**No explicit circular dependencies found**, but there is **implicit coupling**:

1. **Router → Routes → Controllers → Services → Repositories → Models**
   - This is acceptable layering, but routes are dynamically loaded which creates runtime coupling

2. **Dynamic Module Loading**
   - `core/router.py` uses `dynamic_import` to load routes
   - Routes are discovered at runtime, making dependencies implicit
   - **Issue:** Hard to trace dependencies statically

3. **Model Registration**
   - `core/utils/model.py` dynamically loads all models
   - Models must be imported to register with SQLAlchemy
   - **Issue:** Import order matters, but not enforced

---

## Architecture Issues

### 1. No Domain Separation

**Problem:** Admin and User domains share the same models, services, and routes.

**Evidence:**
- `core/routes/admin/user_route.py` uses same `User` model as `core/routes/user/user_route.py`
- `get_current_active_superuser` is just a wrapper around `get_current_user`
- No separate AdminUser model

**Impact:** Impossible to enforce proper isolation between admin and user operations.

---

### 2. Missing RBAC Infrastructure

**Problem:** No role-based access control system exists.

**Evidence:**
- Only `is_superuser` boolean flag on User model
- `require_roles()` function checks for attributes on User model (not actual roles)
- No Permission, Role, or RolePermission models
- No team/tenant isolation

**Impact:** Cannot implement fine-grained permissions or multi-tenant isolation.

---

### 3. Chainlit Integration Pollutes Core

**Problem:** Chainlit-specific fields in User model.

**Evidence:**
```python
# swx_api/core/models/user.py
identifier: Optional[str] = Field(default=None, unique=True, index=True)  # Chainlit
user_metadata: dict = Field(default_factory=dict, ...)  # Chainlit
```

**Impact:** Framework is coupled to a demo application.

---

### 4. Dynamic Route Loading Creates Magic

**Problem:** Routes are discovered and registered automatically.

**Evidence:**
- `core/router.py` scans directories and auto-registers routes
- Admin routes are protected by checking if "admin" is in the path
- No explicit route registration

**Impact:** Hard to understand what routes exist, hard to test, implicit behavior.

---

### 5. No Team/Tenant Isolation

**Problem:** No multi-tenancy support.

**Evidence:**
- No Team model
- No TeamMember model
- No tenant_id or team_id on resources
- All users share the same data space

**Impact:** Cannot support SaaS multi-tenant applications.

---

## Recommendations

### Immediate Actions

1. **Delete Chainlit**
   - Remove `chainlit` dependency from `pyproject.toml`
   - Remove Chainlit fields from User model
   - Delete `scripts/chainlit_app.py`
   - Remove Chainlit mount from `core/main.py`
   - Delete Chainlit migrations

2. **Move Application Code to Example**
   - Move `swx_api/app/` → `swx_app/`
   - Move `core/models/language.py` → `swx_app/models/`
   - Move language-related services/repositories/controllers → `swx_app/`

3. **Separate Admin and User Domains**
   - Create `AdminUser` model (separate from `User`)
   - Create `auth/admin/` and `auth/user/` modules
   - Separate admin routes from user routes with clear boundaries

4. **Implement RBAC**
   - Create Permission, Role, RolePermission models
   - Create Team, TeamMember, TeamRole models
   - Implement permission-checking helpers

5. **Refactor Structure**
   - `swx_core/` - Framework code
   - `swx_app/` - Example application
   - Clear separation of concerns

---

## Proposed New Structure

```
swx_core/
  ├── auth/
  │   ├── core/          # Shared auth utilities
  │   ├── admin/         # Admin authentication
  │   └── user/          # User authentication
  ├── database/
  ├── middleware/
  ├── models/
  │   ├── base.py
  │   ├── permission.py
  │   ├── role.py
  │   ├── team.py
  │   └── user.py        # Framework User (no Chainlit)
  ├── rbac/              # RBAC helpers
  ├── routes/
  │   ├── admin/         # Admin routes
  │   └── user/         # User routes
  ├── security/
  └── cli/

swx_app/
  ├── models/
  ├── services/
  ├── repositories/
  └── routes/
```

---

## Dead Code Identification

### Files to Delete

1. `scripts/chainlit_app.py` - Chainlit demo
2. `chainlit.md` - Chainlit documentation
3. `migrations/versions/c8216b666f9e_create_chainlit_tables_threads_steps_.py` - Chainlit migration
4. Any Chainlit-related migration code in other migration files

### Unused Imports/Code

- Review all files for unused imports (use `ruff` or `mypy`)
- Remove commented-out code blocks

---

## Conclusion

The codebase has a solid foundation but needs significant refactoring to become a reusable framework. The main issues are:

1. **No domain separation** - Admin and user code is mixed
2. **No RBAC** - Only boolean superuser flag
3. **Chainlit pollution** - Demo code in framework
4. **No multi-tenancy** - Cannot support SaaS use cases
5. **Implicit magic** - Dynamic loading makes dependencies unclear

**Next Steps:** Proceed with security audit, then RBAC audit, then begin refactoring.
