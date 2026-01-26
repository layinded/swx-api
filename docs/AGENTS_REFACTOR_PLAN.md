# Agents Refactor Plan

This document outlines a phased plan to bring the SwX-API codebase into closer alignment with the governance rules defined in `.agents/`.

## Phase 1: Technical Debt Remediation (`swx_app`)

**Objective**: Clean up high-risk architectural violations in the application layer.
**Rules Addressed**: Separation of concerns, Type hints, Functional patterns.
**Affected Files**: `swx_app/routes/qa_article_route.py`, `swx_app/controllers/qa_article_controller.py`, `swx_app/services/qa_article_service.py`, `swx_app/repositories/qa_article_repository.py`.

### Actions:
1. **Refactor `QaArticleRepository`**:
    - Move SQL logic from `qa_article_route.py` (`/ask`, `/ollama/generate`) into functions in `qa_article_repository.py`.
    - Convert class-based repository to a module with pure functions.
2. **Refactor `QaArticleService`**:
    - Encapsulate LLM prompt building and business logic.
    - Convert class-based service to a module with pure functions.
3. **Refactor `QaArticleController`**:
    - Remove class wrapper, use pure functions.
    - Ensure all controllers have proper type hints for return values.
4. **Refactor `QaArticleRoute`**:
    - Use Pydantic models for `/ask` and `/ollama/generate` payloads instead of `dict`.
    - Move all logic out of route handlers into the controller/service.

## Phase 2: Core Standardization

**Objective**: Improve consistency of type hints and documentation in `swx_core`.
**Rules Addressed**: Type hints, Docstrings.
**Affected Files**: Various files in `swx_core/repositories/`, `swx_core/services/`.

### Actions:
1. **Audit Type Hints**: Ensure all functions in `swx_core` have explicit return type hints (e.g., `-> User | None` instead of implicit).
2. **Standardize Docstrings**: Ensure consistent Google/Sphinx style docstrings as per rules.

## Phase 3: Governance Alignment (Rule Hardening)

**Objective**: Resolve conflicts between the rules and the reality of the project.
**Rules Addressed**: Dependency Management, Auth, Directory Structure.

### Actions:
1. **Update `.agents` Rules**:
    - Align dependency management rules with `uv`.
    - Update directory structure rules to reflect `swx_core`/`swx_app` split.
    - Document the exception for custom RBAC/Auth system.

---

## Risk Assessment & Rollback

- **Risk Level**: Medium (primarily structural changes in `swx_app`).
- **Safety**: Existing `user_simulation_smoke_test.sh` will be used to ensure no regressions in auth/RBAC.
- **Rollback Point**: Each file refactor can be reverted individually via git.
