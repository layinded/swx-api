# RBAC Audit Report

**Date:** 2024  
**Auditor:** Staff-level Backend Architect  
**Scope:** Critical analysis of Role-Based Access Control implementation

---

## Executive Summary

**This codebase has NO RBAC implementation.** There is only a boolean `is_superuser` flag on the User model. The `require_roles()` function is a **fake implementation** that checks for non-existent attributes.

**Critical Findings:**
1. **No RBAC models exist** - No Permission, Role, RolePermission, UserRole models
2. **Fake role checking** - `require_roles()` checks attributes that don't exist
3. **No permission system** - Cannot implement fine-grained permissions
4. **No team/tenant isolation** - Cannot support multi-tenant applications
5. **Global roles only** - No scoped roles (team-specific, resource-specific)
6. **Admin/user confusion** - Same User model for both domains

---

## Current "RBAC" Implementation Analysis

### What Exists

#### 1. Boolean Superuser Flag

**File:** `swx_api/core/models/user.py:45`

```python
is_superuser: bool = False
```

**Analysis:**
- ✅ Simple and works for basic admin checks
- ❌ Not scalable - only two states (admin or not)
- ❌ Cannot implement fine-grained permissions
- ❌ Cannot have multiple admin roles (e.g., "content_admin", "user_admin")
- ❌ Cannot have team-scoped admin roles

**Verdict:** Acceptable for MVP, unacceptable for production framework.

---

#### 2. Fake Role Checking Function

**File:** `swx_api/core/security/dependencies.py:114-154`

```python
def require_roles(*roles):
    def role_checker(current_user: CurrentUser, request: Request) -> User:
        if not any(getattr(current_user, role, False) for role in roles):
            raise HTTPException(...)
        return current_user
    return role_checker
```

**Analysis:**
- ❌ **BROKEN** - Checks for attributes on User model (e.g., `user.admin`, `user.moderator`)
- ❌ These attributes **do not exist** on the User model
- ❌ Only `is_superuser` exists, so `require_roles("admin")` will always fail
- ❌ No actual role checking happens
- ❌ Misleading function name suggests RBAC exists

**Example:**
```python
# This will ALWAYS fail because User model has no "admin" attribute
@router.get("/admin/dashboard", dependencies=[Depends(require_roles("admin"))])
def admin_dashboard():
    ...
```

**Verdict:** **This is broken code that should be deleted immediately.**

---

#### 3. Admin User Dependency

**File:** `swx_api/core/security/dependencies.py:88-111`

```python
def get_current_active_superuser(current_user: CurrentUser, request: Request) -> User:
    if not current_user.is_superuser:
        raise HTTPException(...)
    return current_user
```

**Analysis:**
- ✅ Works correctly for admin checks
- ❌ Only checks boolean flag, not actual permissions
- ❌ No distinction between different admin roles
- ❌ Cannot have scoped admin access (e.g., admin of Team A but not Team B)

**Verdict:** Acceptable for basic admin checks, insufficient for framework.

---

## What's Missing

### 1. No Permission Model

**Required Models:**
```python
class Permission(SQLModel, table=True):
    id: UUID
    name: str  # e.g., "user:read", "user:write", "article:delete"
    description: str
    resource_type: str  # e.g., "user", "article", "team"
    action: str  # e.g., "read", "write", "delete"
```

**Impact:** Cannot implement fine-grained permissions. Everything is all-or-nothing.

---

### 2. No Role Model

**Required Models:**
```python
class Role(SQLModel, table=True):
    id: UUID
    name: str  # e.g., "admin", "moderator", "editor"
    description: str
    is_system_role: bool  # System roles vs custom roles
    domain: str  # "admin", "user", "system"
```

**Impact:** Cannot define roles. Cannot assign multiple roles to users.

---

### 3. No Role-Permission Mapping

**Required Models:**
```python
class RolePermission(SQLModel, table=True):
    role_id: UUID
    permission_id: UUID
```

**Impact:** Cannot associate permissions with roles. Cannot build permission hierarchies.

---

### 4. No User-Role Assignment

**Required Models:**
```python
class UserRole(SQLModel, table=True):
    user_id: UUID
    role_id: UUID
    # For scoped roles:
    team_id: Optional[UUID]  # Team-scoped role
    resource_id: Optional[UUID]  # Resource-scoped role
```

**Impact:** Cannot assign roles to users. Cannot have team-scoped roles.

---

### 5. No Team/Tenant Isolation

**Required Models:**
```python
class Team(SQLModel, table=True):
    id: UUID
    name: str
    tenant_id: Optional[UUID]  # For multi-tenant support

class TeamMember(SQLModel, table=True):
    team_id: UUID
    user_id: UUID
    role_id: UUID  # Team-scoped role
```

**Impact:** Cannot support multi-tenant applications. Cannot isolate data by team.

---

### 6. No Permission Checking Helpers

**Required Functions:**
```python
def require_permission(permission: str):
    """Check if user has specific permission"""
    
def require_role(role: str, domain: str = "user"):
    """Check if user has specific role in domain"""
    
def require_team_permission(team_id: UUID, permission: str):
    """Check if user has permission in specific team"""
```

**Impact:** Cannot check permissions in routes. Must manually check everywhere.

---

## Design Problems

### Problem 1: Role vs Permission Confusion

**Current State:** No distinction between roles and permissions. Everything is a boolean flag.

**Required Design:**
- **Permissions** are atomic actions (e.g., "user:read", "article:delete")
- **Roles** are collections of permissions (e.g., "admin" = all permissions, "editor" = read/write articles)
- **Users** have roles, roles have permissions

**Impact:** Cannot implement least-privilege principle. Cannot have granular access control.

---

### Problem 2: Global Roles Only

**Current State:** `is_superuser` is global - user is admin of everything or nothing.

**Required Design:**
- **Global roles:** Apply to entire system (e.g., "system_admin")
- **Team-scoped roles:** Apply to specific team (e.g., "team_admin" for Team A)
- **Resource-scoped roles:** Apply to specific resource (e.g., "owner" of Article X)

**Impact:** Cannot support multi-tenant applications. Cannot have team-based access control.

---

### Problem 3: Admin vs User Domain Confusion

**Current State:** Same User model for admin and user domains. Same authentication flow.

**Required Design:**
- **AdminUser** - Separate model for admin users
- **User** - Regular application users
- **SystemUser** - Internal system users (CLI, background jobs)
- Separate authentication flows for each domain

**Impact:** Cannot enforce proper isolation. Admin users can access user endpoints and vice versa.

---

### Problem 4: Missing Tenant Isolation

**Current State:** No tenant_id or team_id on resources. All users share same data space.

**Required Design:**
- **Team** model for grouping users
- **TeamMember** model for user-team relationships
- **TeamRole** model for team-scoped roles
- Resources belong to teams (or have team_id)

**Impact:** Cannot support SaaS multi-tenant applications. Data leakage risk.

---

## Bad Design Patterns

### Pattern 1: Fake Role Checking

**Location:** `swx_api/core/security/dependencies.py:114`

**Problem:** Function suggests RBAC exists but is completely broken.

**Code:**
```python
def require_roles(*roles):
    # This checks for attributes that don't exist!
    if not any(getattr(current_user, role, False) for role in roles):
        raise HTTPException(...)
```

**Why It's Bad:**
- Misleading - suggests RBAC exists
- Broken - will always fail
- No error message indicates the real problem
- Developers will waste time trying to use it

**Fix:** Delete this function. Implement proper permission checking.

---

### Pattern 2: String-Based Admin Protection

**Location:** `swx_api/core/router.py:88`

**Problem:** Admin protection based on string matching path.

**Code:**
```python
if "admin" in user_defined_prefix.lower():
    module.router.dependencies.extend([Depends(get_current_active_superuser)])
```

**Why It's Bad:**
- Fragile - breaks if path doesn't contain "admin"
- Implicit - easy to miss protection
- No explicit opt-in required
- Can be bypassed with creative naming

**Fix:** Require explicit `AdminUser` dependency on all admin routes.

---

### Pattern 3: Manual Access Checks

**Location:** `swx_api/core/routes/user/user_route.py:96`

**Problem:** Access control implemented per-route with manual checks.

**Code:**
```python
if current_user.id != user_id:
    raise HTTPException(status_code=403, detail="access_denied")
```

**Why It's Bad:**
- Easy to forget checks in new routes
- Inconsistent error messages
- No centralized permission logic
- Hard to test

**Fix:** Implement permission decorators or dependencies.

---

## Required RBAC Implementation

### 1. Permission-First Design

**Principle:** Permissions are explicit strings. Roles are collections of permissions.

**Models:**
```python
class Permission(SQLModel, table=True):
    id: UUID
    name: str  # "user:read", "article:delete"
    resource_type: str
    action: str

class Role(SQLModel, table=True):
    id: UUID
    name: str
    domain: str  # "admin", "user", "system"
    is_system_role: bool

class RolePermission(SQLModel, table=True):
    role_id: UUID
    permission_id: UUID

class UserRole(SQLModel, table=True):
    user_id: UUID
    role_id: UUID
    team_id: Optional[UUID]  # For scoped roles
```

---

### 2. Domain Separation

**Admin Domain:**
- `AdminUser` model (separate from User)
- `AdminRole` model (admin-specific roles)
- `AdminPermission` model (admin-specific permissions)
- Separate authentication flow

**User Domain:**
- `User` model (regular users)
- `UserRole` model (user roles)
- `UserPermission` model (user permissions)
- Separate authentication flow

**System Domain:**
- `SystemUser` model (internal users)
- No HTTP session assumption
- Explicit scopes only

---

### 3. Team/Tenant Isolation

**Models:**
```python
class Team(SQLModel, table=True):
    id: UUID
    name: str
    tenant_id: Optional[UUID]

class TeamMember(SQLModel, table=True):
    team_id: UUID
    user_id: UUID
    role_id: UUID  # Team-scoped role

class TeamRole(SQLModel, table=True):
    team_id: UUID
    role_id: UUID
    # Team-specific role configuration
```

**Permission Checking:**
```python
def require_team_permission(team_id: UUID, permission: str):
    """Check if user has permission in team"""
    # 1. Check if user is team member
    # 2. Check if user's team role has permission
    # 3. Check if user has global permission
```

---

### 4. Permission Helpers

**Functions:**
```python
def has_permission(user: User, permission: str) -> bool:
    """Check if user has permission (via roles)"""
    
def require_permission(permission: str):
    """FastAPI dependency to require permission"""
    
def require_team_permission(team_id: UUID, permission: str):
    """FastAPI dependency to require team permission"""
    
def require_role(role: str, domain: str = "user"):
    """FastAPI dependency to require role"""
```

---

## Recommendations

### Immediate Actions

1. **Delete `require_roles()` function** - It's broken and misleading
2. **Document that RBAC does not exist** - Be honest about current state
3. **Plan proper RBAC implementation** - Design before coding

### High Priority

1. **Implement Permission model** - Foundation for RBAC
2. **Implement Role model** - Collections of permissions
3. **Implement RolePermission mapping** - Associate permissions with roles
4. **Implement UserRole assignment** - Assign roles to users

### Medium Priority

1. **Implement Team/Tenant isolation** - For multi-tenant support
2. **Separate Admin and User domains** - Clear boundaries
3. **Implement permission helpers** - Reusable permission checking

### Low Priority

1. **Add permission caching** - Performance optimization
2. **Add permission inheritance** - Hierarchical permissions
3. **Add permission delegation** - Advanced use cases

---

## Conclusion

**This codebase has NO RBAC implementation.** The `require_roles()` function is broken and should be deleted. The `is_superuser` flag is insufficient for a production framework.

**Required Implementation:**
1. Permission-first RBAC model
2. Separate Admin and User domains
3. Team/Tenant isolation
4. Proper permission checking helpers

**Next Steps:** Proceed with refactoring to implement proper RBAC as part of framework hardening.
