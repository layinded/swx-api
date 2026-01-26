# Agents Rules Inventory

This document lists all the rules found in the `.agents/` directory, categorized by their source file, scope, and intent.

## 1. python-312-fastapi-best-practices-cursorrules-prompt.md

- **Name**: Python 3.12 & FastAPI Best Practices
- **Scope**: Backend Development (Python, FastAPI, Database)
- **Intent**: Establish a baseline for modern Python/FastAPI development using a specific set of libraries and coding standards.
- **Enforced or Advisory**: Primarily Enforced (use of "must follow").
- **Expected Code Patterns**:
    - Python 3.12 features.
    - Specific libraries: `pydantic`, `fastapi`, `sqlalchemy`, `poetry`, `alembic`, `fastapi-users`, `fastapi-jwt-auth`, `fastapi-mail`, `fastapi-cache`, `fastapi-limiter`, `fastapi-pagination`.
    - Meaningful names, PEP 8, Docstrings, Simple code, List comprehensions, Exception handling, Virtual environments, Unit tests, Type hints, No global variables.

## 2. python-fastapi-scalable-api-cursorrules-prompt-file.md

- **Name**: Scalable API Development Guide
- **Scope**: Fullstack (Python Backend + TypeScript/React Frontend)
- **Intent**: Provide principles for building scalable, high-performance applications with a focus on modularization and functional patterns.
- **Enforced or Advisory**: Enforced.
- **Expected Code Patterns**:
    - **General**: Functional and declarative patterns, modularization, descriptive names with auxiliary verbs (`is_active`).
    - **Backend**: `def` for pure functions, `async def` for I/O, Type hints for everything, Pydantic models for validation, Clear directory separation (`routes`, `utils`, `models`), RORO pattern, Early returns/Guard clauses, Proper logging.
    - **Directory Structure**: Backend source in `backend/src/`.
    - **Performance**: Asynchronous operations, Caching, Lazy loading.
    - **Conventions**: RESTful API design, FastAPI Dependency Injection, SQLAlchemy 2.0.

## 3. python-projects-guide-cursorrules-prompt-file.md

- **Name**: Python Projects Guide
- **Scope**: Project Lifecycle & Governance
- **Intent**: standardize project structure, dependency management, and quality assurance processes.
- **Enforced or Advisory**: Enforced.
- **Expected Code Patterns**:
    - Clear structure (source, tests, docs, config).
    - Modular design (models, services, controllers, utilities).
    - Environment variables for config.
    - `pytest` for testing.
    - `rye` for dependency management.
    - `Ruff` for style/linting.
    - CI/CD implementation.
    - AI-friendly practices: Descriptive names, Type hints, Detailed comments, Rich error context.

---

## Summary of Potential Conflicts

1. **Dependency Management**: File 1 specifies `poetry`, File 3 specifies `rye`. The actual project uses `uv`.
2. **Directory Structure**: File 2 specifies `backend/src/`. The actual project uses `swx_core/` and `swx_app/`.
3. **Authentication**: File 1 specifies `fastapi-users` and `fastapi-jwt-auth`. The actual project uses a custom implementation.
4. **Library Selection**: File 1 specifies many specific `fastapi-*` plugins which might not be present or desired if custom solutions are implemented.
