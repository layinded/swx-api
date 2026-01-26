# CLI Hardening - Complete

**Date:** 2024  
**Status:** ✅ Complete

---

## Summary

Successfully hardened the CLI scaffolding tools to enforce secure patterns and prevent insecure code generation.

---

## Security Enhancements

### 1. Security Validation Module ✅

Created `swx_core/cli/commands/security_validation.py` with:

- **Dangerous Field Name Detection:**
  - Blocks fields like `is_superuser`, `is_admin`, `hashed_password`, `secret_key`, etc.
  - Prevents privilege escalation patterns
  - Blocks password/token handling outside framework utilities

- **Dangerous Resource Name Detection:**
  - Blocks reserved names like `user`, `admin`, `permission`, `role`, `auth`, `security`
  - Prevents conflicts with framework security modules

- **Module Path Validation:**
  - Prevents creating resources in `swx_core.*` namespace
  - Enforces use of `swx_app.*` or custom app namespaces

### 2. Input Validation in CLI Commands ✅

Updated all CLI commands to validate inputs:

- **`model` command:**
  - Validates resource name
  - Validates module path
  - Validates each field name
  - Validates all columns together

- **`controller` command:**
  - Validates resource name
  - Validates module path

- **`route` command:**
  - Validates resource name
  - Validates module path

- **`make-from-model` command:**
  - Validates resource name
  - Validates module path

### 3. Route Template Security Warnings ✅

Updated route template to include:

- **Security warnings** in generated code
- **TODO comments** reminding developers to add authentication
- **Example imports** for authentication dependencies
- **Clear documentation** that routes are NOT protected by default

### 4. Lint Command Fix ✅

Fixed lint command to check both:
- `swx_core/` (framework code)
- `swx_app/` (application code)

---

## Security Validations

### Blocked Field Names

The following field names are blocked:
- `is_superuser`, `is_admin`, `is_staff`, `is_administrator`
- `has_admin_access`, `admin`, `superuser`, `root`
- `password_hash`, `hashed_password`
- `secret_key`, `api_key`, `access_token`, `refresh_token`, `token`

### Blocked Resource Names

The following resource names are blocked:
- `user`, `admin`, `adminuser`, `admin_user`, `superuser`
- `permission`, `role`, `token`
- `auth`, `security`

### Blocked Module Paths

The following module paths are blocked:
- `swx_core.models`
- `swx_core.auth`
- `swx_core.security`
- `swx_core.rbac`
- Any path starting with `swx_core.*`

---

## Example Error Messages

When a user tries to create an insecure pattern:

```bash
$ swx make model User --columns "email:str,is_superuser:bool"
❌ Security Error: Resource name 'User' is reserved. Use a different name.

$ swx make model Product --columns "name:str,is_admin:bool"
❌ Security Error: Field name 'is_admin' is reserved for security reasons. Use a different name.

$ swx make model Product --module swx_core.models
❌ Security Error: Module path 'swx_core.models' is reserved for framework use. Use 'swx_app.models' or your own app namespace.
```

---

## Generated Code Security

### Route Template

Generated routes now include:
- Security warnings at the top
- TODO comments for authentication
- Example imports commented out
- Clear documentation that routes are unprotected by default

Example generated route:
```python
# SECURITY NOTE: This route template does NOT include authentication by default.
# You MUST add authentication dependencies to protect your routes.

# TODO: Add authentication dependency
# from swx_core.auth.user.dependencies import UserDep
# from swx_core.rbac.dependencies import require_permission

@router.get("/", response_model=list[ProductPublic])
def get_all(request: Request, db: SessionDep,
            # TODO: Add authentication: current_user: UserDep,
            skip: int = Query(0), limit: int = Query(100)):
    return ProductController.retrieve_all_product_resources(request, db, skip=skip, limit=limit)
```

---

## Verification

- ✅ All CLI commands validate inputs
- ✅ Security validation module created
- ✅ Route templates include security warnings
- ✅ Lint command checks both directories
- ✅ No linter errors
- ✅ All dangerous patterns blocked

---

## Status

✅ **CLI hardening is complete!**

The CLI now:
- Prevents insecure patterns from being generated
- Validates all inputs before code generation
- Warns developers about missing authentication
- Enforces secure coding practices
