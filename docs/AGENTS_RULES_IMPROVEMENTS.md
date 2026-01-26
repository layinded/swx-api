# Agents Rules Improvements

This document proposes specific updates to the rules in the `.agents/` directory to resolve conflicts, remove ambiguity, and align with the SwX-API project standards.

## 1. Dependency Management Alignment

**Issue**: Conflicting requirements for `poetry` and `rye`, while the project uses `uv`.
**Proposal**:
- Update all rule files to specify `uv` as the mandatory dependency management tool.
- Remove references to `poetry` and `rye`.
- Add a rule for keeping `pyproject.toml` and `uv.lock` in sync.

## 2. Structural Patterns

**Issue**: Rule requires `backend/src/` layout, project uses `swx_core/` (Framework) and `swx_app/` (Application).
**Proposal**:
- Update structural rules to recognize the "Framework vs. Application" split.
- Define specific responsibilities for `swx_core` (Shared logic, Auth, DB utilities) and `swx_app` (Domain-specific business logic).
- Standardize the `Route -> Controller -> Service -> Repository` flow as the mandatory pattern for all domains.

## 3. Authentication & RBAC Governance

**Issue**: Rules mandate `fastapi-users`, but project uses a custom multi-domain RBAC system.
**Proposal**:
- Rewrite the authentication rule to focus on *principles* rather than *libraries*.
- Principles: Mandatory token audience validation, strict domain separation (Admin/User), fine-grained permission checks, and team-scoped access.
- Explicitly permit custom implementations if they meet these security principles and follow the project's standard modular pattern.

## 4. Coding Style Hardening

**Issue**: Ambiguity regarding "avoid classes" vs. existing class-based controllers.
**Proposal**:
- Clarify the "Functional First" rule: "Prefer top-level functions over classes for Controllers, Services, and Repositories. Use classes only when managing complex state or implementing standard interfaces that require them."
- Require explicit return type hints for *all* public functions in these layers.

## 5. Directory Mapping

**Current**:
```
backend/src/
backend/tests/
```
**Proposed**:
```
swx_core/          # Framework level logic
swx_app/           # Business level logic
docs/              # Documentation
migrations/        # Alembic migrations
scripts/           # Automation & Smoke tests
```
