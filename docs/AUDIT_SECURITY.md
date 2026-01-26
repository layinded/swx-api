# Security Audit Report

**Date:** 2024  
**Auditor:** Staff-level Security Engineer  
**Scope:** Full security audit of authentication, authorization, and access control

---

## Executive Summary

This codebase has **critical security vulnerabilities** that must be addressed before production use. The authentication system is fundamentally flawed, with no proper RBAC, weak token handling, and multiple privilege escalation risks.

**Critical Vulnerabilities:**
1. **No RBAC** - Only boolean `is_superuser` flag
2. **Token scope confusion** - Same tokens for admin and user
3. **Missing permission checks** - Routes rely on implicit checks
4. **Admin/user domain confusion** - No clear boundaries
5. **Weak JWT validation** - Missing audience checks, scope validation
6. **Registration allows superuser creation** - Default `is_superuser=True` in UserCreate
7. **No token revocation for access tokens** - Only refresh tokens are revocable

---

## Critical Vulnerabilities

### 1. Registration Allows Superuser Creation (CRITICAL)

**File:** `swx_api/core/models/user.py:101`

```python
class UserCreate(SQLModel):
    is_superuser: Optional[bool] = Field(default=True)  # ⚠️ CRITICAL
```

**Issue:** User registration schema defaults `is_superuser=True`, allowing anyone to create admin accounts.

**Evidence:**
- `swx_api/core/routes/access/auth_route.py:80` - Public registration endpoint
- No validation preventing superuser creation via registration

**Impact:** **CRITICAL** - Unauthorized users can create admin accounts.

**Fix:**
- Remove `is_superuser` from `UserCreate` schema
- Only allow superuser creation via admin endpoints or CLI
- Add validation to reject `is_superuser=True` in registration

---

### 2. No Token Audience Validation (HIGH)

**File:** `swx_api/core/security/dependencies.py:56-60`

```python
payload = jwt.decode(
    token,
    settings.SECRET_KEY,
    algorithms=[settings.PASSWORD_SECURITY_ALGORITHM],
)
```

**Issue:** JWT tokens are decoded without checking `aud` (audience) claim. Admin and user tokens use the same secret key and are indistinguishable.

**Evidence:**
- `create_access_token()` in `refresh_token_service.py:28-50` does not set `aud` claim
- `get_current_user()` does not validate token audience
- Same token can be used for both admin and user endpoints

**Impact:** **HIGH** - User tokens can potentially access admin endpoints if route protection fails.

**Fix:**
- Add `aud` claim to tokens (e.g., "admin", "user", "system")
- Validate `aud` in token validation
- Use different secret keys or explicit audience validation

---

### 3. No Token Scope Validation (HIGH)

**File:** `swx_api/core/security/dependencies.py:37-81`

**Issue:** Tokens contain no scope/permission information. All authorization is based on database lookups.

**Evidence:**
- Token payload only contains `sub` (email) and `auth_provider`
- No `scope` or `permissions` claims
- Every request requires database lookup to check permissions

**Impact:** **HIGH** - Cannot revoke access tokens, cannot implement fine-grained permissions, performance impact.

**Fix:**
- Add `scope` claim to tokens with explicit permissions
- Validate scopes in dependency functions
- Support token revocation via blacklist or short expiration

---

### 4. Weak Admin Route Protection (HIGH)

**File:** `swx_api/core/router.py:88-90`

```python
if "admin" in user_defined_prefix.lower():
    module.router.dependencies.extend([Depends(get_current_active_superuser)])
```

**Issue:** Admin route protection is based on **string matching** the path prefix. This is fragile and can be bypassed.

**Evidence:**
- Routes with "admin" in path are protected, but this is implicit
- No explicit route registration
- Easy to miss protection if route doesn't match pattern

**Impact:** **HIGH** - Admin routes may be unprotected if naming convention is not followed.

**Fix:**
- Remove implicit admin protection
- Require explicit `AdminUser` dependency on all admin routes
- Fail closed - require explicit opt-in for admin access

---

### 5. Role Checking Uses Attribute Lookup (MEDIUM)

**File:** `swx_api/core/security/dependencies.py:147`

```python
if not any(getattr(current_user, role, False) for role in roles):
```

**Issue:** `require_roles()` checks for attributes on User model, not actual roles. This is not a real RBAC system.

**Evidence:**
- No Role model exists
- No Permission model exists
- `require_roles("admin")` checks `user.admin` attribute (which doesn't exist)
- Only `is_superuser` attribute exists, so role checks are broken

**Impact:** **MEDIUM** - Role-based access control does not work. Only `is_superuser` check works.

**Fix:**
- Implement proper RBAC with Permission and Role models
- Replace `require_roles()` with permission-based checks
- Remove fake role checking

---

### 6. No Access Token Revocation (MEDIUM)

**File:** `swx_api/core/security/refresh_token_service.py`

**Issue:** Access tokens cannot be revoked. Only refresh tokens are stored in database and can be revoked.

**Evidence:**
- Access tokens are stateless JWTs
- No blacklist or revocation mechanism
- Tokens valid until expiration even if user is deactivated

**Impact:** **MEDIUM** - Compromised tokens remain valid until expiration. Cannot revoke access immediately.

**Fix:**
- Implement token blacklist (Redis or database)
- Check blacklist in `get_current_user()`
- Support immediate revocation

---

### 7. Password Reset Token Uses Same Secret (MEDIUM)

**File:** `swx_api/core/security/password_security.py:78-82`

```python
encoded_jwt = jwt.encode(
    {"exp": expires.timestamp(), "sub": email, "auth_provider": "local"},
    settings.SECRET_KEY,  # ⚠️ Same key as access tokens
    algorithm=settings.PASSWORD_SECURITY_ALGORITHM,
)
```

**Issue:** Password reset tokens use the same secret key as access tokens. If reset token is leaked, it could be confused with access token.

**Evidence:**
- Same `SECRET_KEY` used for access tokens and reset tokens
- No `aud` claim to distinguish token types
- Reset tokens could potentially be used as access tokens (if validation is bypassed)

**Impact:** **MEDIUM** - Token type confusion risk.

**Fix:**
- Use separate secret key for reset tokens
- Add explicit `aud` claim ("password_reset")
- Validate `aud` in reset token verification

---

### 8. User Can Access Other Users' Data (MEDIUM)

**File:** `swx_api/core/routes/user/user_route.py:74-98`

```python
@router.get("/{user_id}", response_model=UserPublic, operation_id="get_user_by_id")
def read_user_by_id(user_id: UUID, ...):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail=translate(request, "access_denied"))
```

**Issue:** Access control is implemented **per-route** with manual checks. Easy to forget checks in new routes.

**Evidence:**
- Manual `if current_user.id != user_id` checks
- No centralized permission checking
- Easy to miss checks in new endpoints

**Impact:** **MEDIUM** - Risk of missing access checks in new routes.

**Fix:**
- Implement permission decorators or dependencies
- Centralize permission checking logic
- Add automated tests for access control

---

### 9. No Rate Limiting (LOW)

**Issue:** No rate limiting on authentication endpoints.

**Evidence:**
- Login endpoint has no rate limiting
- Password reset endpoint has no rate limiting
- Registration endpoint has no rate limiting

**Impact:** **LOW** - Vulnerable to brute force attacks and abuse.

**Fix:**
- Add rate limiting middleware
- Limit login attempts per IP
- Limit password reset requests per email

---

### 10. Insecure Defaults (LOW)

**File:** `swx_api/core/config/settings.py:164-165`

```python
FIRST_SUPERUSER: str = "admin@example.com"
FIRST_SUPERUSER_PASSWORD: str = "securepassword"
```

**Issue:** Default superuser credentials are weak and predictable.

**Evidence:**
- Hardcoded default credentials
- Weak default password
- Predictable email

**Impact:** **LOW** - Risk if defaults are not changed in production.

**Fix:**
- Require strong password in production
- Generate random password if not set
- Fail startup if weak credentials detected in production

---

## Security Issues by Category

### Authentication

1. ✅ **Password Hashing:** Uses bcrypt (secure)
2. ❌ **Token Validation:** Missing audience and scope checks
3. ❌ **Token Revocation:** Access tokens cannot be revoked
4. ❌ **Token Type Confusion:** Reset tokens use same secret as access tokens

### Authorization

1. ❌ **No RBAC:** Only boolean `is_superuser` flag
2. ❌ **Fake Role Checking:** `require_roles()` checks non-existent attributes
3. ❌ **Weak Admin Protection:** Based on string matching path
4. ❌ **Manual Access Checks:** Per-route checks, easy to miss

### Access Control

1. ❌ **No Permission System:** Cannot implement fine-grained permissions
2. ❌ **No Team/Tenant Isolation:** All users share same data space
3. ❌ **Admin/User Confusion:** Same models and services for both domains
4. ⚠️ **Registration Security:** Allows superuser creation

### Token Security

1. ✅ **Refresh Token Storage:** Stored in database (revocable)
2. ❌ **Access Token Stateless:** Cannot be revoked
3. ❌ **No Token Blacklist:** Cannot revoke compromised tokens
4. ❌ **No Audience Validation:** Tokens not scoped to domains

---

## Detailed Vulnerability List

### VULN-001: Registration Allows Superuser Creation
- **Severity:** CRITICAL
- **File:** `swx_api/core/models/user.py:101`
- **Description:** `UserCreate` schema defaults `is_superuser=True`
- **Fix:** Remove from schema, only allow via admin endpoints

### VULN-002: No Token Audience Validation
- **Severity:** HIGH
- **File:** `swx_api/core/security/dependencies.py:56`
- **Description:** JWT tokens decoded without `aud` claim validation
- **Fix:** Add `aud` claim and validate in token decoding

### VULN-003: No Token Scope Validation
- **Severity:** HIGH
- **File:** `swx_api/core/security/refresh_token_service.py:28`
- **Description:** Tokens contain no scope/permission information
- **Fix:** Add `scope` claim with explicit permissions

### VULN-004: Weak Admin Route Protection
- **Severity:** HIGH
- **File:** `swx_api/core/router.py:88`
- **Description:** Admin protection based on string matching path
- **Fix:** Require explicit `AdminUser` dependency

### VULN-005: Fake Role Checking
- **Severity:** MEDIUM
- **File:** `swx_api/core/security/dependencies.py:147`
- **Description:** `require_roles()` checks non-existent attributes
- **Fix:** Implement proper RBAC with Permission model

### VULN-006: No Access Token Revocation
- **Severity:** MEDIUM
- **File:** `swx_api/core/security/dependencies.py:37`
- **Description:** Access tokens cannot be revoked
- **Fix:** Implement token blacklist

### VULN-007: Password Reset Token Secret Reuse
- **Severity:** MEDIUM
- **File:** `swx_api/core/security/password_security.py:80`
- **Description:** Reset tokens use same secret as access tokens
- **Fix:** Use separate secret key for reset tokens

### VULN-008: Manual Access Control Checks
- **Severity:** MEDIUM
- **File:** `swx_api/core/routes/user/user_route.py:96`
- **Description:** Access control implemented per-route manually
- **Fix:** Centralize permission checking

### VULN-009: No Rate Limiting
- **Severity:** LOW
- **File:** `swx_api/core/routes/access/auth_route.py`
- **Description:** No rate limiting on auth endpoints
- **Fix:** Add rate limiting middleware

### VULN-010: Insecure Default Credentials
- **Severity:** LOW
- **File:** `swx_api/core/config/settings.py:164`
- **Description:** Weak default superuser credentials
- **Fix:** Require strong passwords, fail on weak defaults in production

---

## Recommendations

### Immediate Fixes (Before Production)

1. **Remove `is_superuser` from UserCreate schema**
2. **Add token audience validation**
3. **Require explicit admin dependencies on admin routes**
4. **Implement token blacklist for access tokens**

### High Priority

1. **Implement proper RBAC** with Permission and Role models
2. **Add token scope validation**
3. **Separate admin and user token secrets/audiences**
4. **Centralize permission checking**

### Medium Priority

1. **Add rate limiting**
2. **Use separate secret for reset tokens**
3. **Add automated access control tests**
4. **Implement team/tenant isolation**

### Low Priority

1. **Harden default credentials**
2. **Add security headers middleware**
3. **Implement CSRF protection**
4. **Add request logging for security events**

---

## Conclusion

This codebase has **critical security vulnerabilities** that must be addressed:

1. **No RBAC** - Cannot implement proper access control
2. **Weak token validation** - Missing audience and scope checks
3. **Registration vulnerability** - Allows superuser creation
4. **Admin/user confusion** - No clear domain boundaries

**Priority:** Fix VULN-001, VULN-002, VULN-003, VULN-004 immediately before any production deployment.

**Next Steps:** Proceed with RBAC audit, then implement fixes in refactoring phase.
