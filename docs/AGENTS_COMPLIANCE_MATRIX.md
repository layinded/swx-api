# Agents Compliance Matrix

This document maps the rules from the `.agents/` directory to the current state of the codebase.

## Compliance Overview

| Rule Category | Compliance Status | Comments |
| :--- | :---: | :--- |
| **Language & Frameworks** | ⚠️ | Using Python 3.12, FastAPI, SQLAlchemy, Alembic. |
| **Dependency Management** | ❌ | Violated: Rules specify `poetry` or `rye`, project uses `uv`. |
| **User & Auth Management** | ❌ | Violated: Rules specify `fastapi-users` and `fastapi-jwt-auth`, project uses custom implementation. |
| **Directory Structure** | ❌ | Violated: Rules specify `backend/src/`, project uses `swx_core/` and `swx_app/`. |
| **Code Style (PEP 8, Ruff)** | ✅ | Generally compliant, enforced by Ruff. |
| **Type Hints** | ⚠️ | Mostly present in `swx_core`, less consistent in `swx_app`. |
| **Docstrings** | ✅ | Consistent use of docstrings across most modules. |
| **Naming Conventions** | ✅ | Good use of descriptive names and auxiliary verbs (`is_active`). |
| **Error Handling** | ✅ | Structured exception handlers in `main.py` and guard clauses in services. |
| **Testing** | ⚠️ | Smoke test script exists, but `pytest` unit tests are sparse or missing for new features. |

## Detailed Violations

### 1. Dependency Management
- **Rule**: "You use poetry for dependency management" / "Dependency management via rye"
- **File**: `pyproject.toml`
- **Status**: ❌ Violated
- **Explanation**: The project uses `uv` as indicated by `uv.lock` and instructions in previous sessions.
- **Risk Level**: Medium (Inconsistency with documented governance, though `uv` is technically superior).

### 2. Authentication & User Management
- **Rule**: "You use fastapi-users for user management", "You use fastapi-jwt-auth for authentication"
- **File**: `swx_core/auth/`, `swx_core/models/user.py`
- **Status**: ❌ Violated
- **Explanation**: The project implements a custom RBAC and JWT authentication system. While robust, it directly contradicts the specific library requirements.
- **Risk Level**: High (Technical debt if the custom solution becomes too complex to maintain compared to standard libraries).

### 3. Backend Directory Structure
- **Rule**: "Directory Structure: backend/src/: Main source code"
- **File**: Root directory
- **Status**: ❌ Violated
- **Explanation**: Code is split between `swx_core/` and `swx_app/`.
- **Risk Level**: Low (Structural preference, but causes friction with rule-following agents).

### 4. Type Hints & Schema Usage
- **Rule**: "Type Hints: Use Python type hints for all function signatures. Prefer Pydantic models for input validation."
- **File**: `swx_app/routes/qa_article_route.py`
- **Snippet**: 
    ```python
    @router.post("/ask")
    def ask_with_rag(payload: dict, db: SessionDep):
    ```
- **Explanation**: Uses `dict` for `payload` instead of a specific Pydantic model. Return type hint is missing.
- **Risk Level**: Medium (Lacks validation, harder for AI/IDE to assist).

### 5. Functional vs Class Patterns
- **Rule**: "Use functional and declarative programming patterns; avoid classes unless absolutely necessary."
- **File**: `swx_app/controllers/qa_article_controller.py`
- **Snippet**:
    ```python
    class QaArticleController:
        @staticmethod
        def retrieve_all_qa_article_search_resources(...):
    ```
- **Explanation**: Uses a class with static methods where plain functions are preferred by the rules.
- **Risk Level**: Low (Style preference, but strictly a violation of "avoid classes").

### 6. Code Duplication / Logic Leak
- **Rule**: "Prefer iteration and modularization over code duplication.", "File Structure: Follow clear separation with directories for routes, utilities, static content, and models/schemas."
- **File**: `swx_app/routes/qa_article_route.py`
- **Explanation**: SQL queries and LLM logic are embedded directly in the route function instead of being encapsulated in a service/repository.
- **Risk Level**: Medium (Harder to test, violates separation of concerns).
