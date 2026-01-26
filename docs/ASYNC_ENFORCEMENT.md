# Async Enforcement Guards

This document outlines the safeguards implemented to prevent regression into synchronous database patterns and to ensure the event loop remains non-blocking.

## 1. Runtime Enforcement

### Engine & Session Isolation
- **Async Engine**: `async_engine` using `asyncpg` is the ONLY engine used by the FastAPI application runtime.
- **Sync Engine**: `engine` using `psycopg` is strictly reserved for:
    - Alembic migrations (`migrations/env.py`)
    - Startup bootstrap scripts (`swx_core/database/db_setup.py`)
    - CLI tools that run outside the main request handling path.

### No Sync in Request path
Any attempt to use a synchronous session within an `async def` route will fail to compile or pass linter checks if type hints are respected.

## 2. Blocking I/O Mitigation

### Password Hashing
Password hashing (bcrypt) is CPU-bound and blocking. It is now offloaded to a threadpool using `asyncio.to_thread`:
```python
async def get_password_hash(password: str) -> str:
    return await asyncio.to_thread(pwd_context.hash, password)
```

### Translation File I/O
Disk I/O for translation loading is mitigated by a global in-memory cache. disk reads only occur once at startup or when the background task explicitly updates the cache.

## 3. Linter & Static Analysis (Recommended)
Future contributors should use Ruff with rules that flag sync I/O in async functions.

## 4. Async Coding Rules
1. Always use `SessionDep` which injects an `AsyncSession`.
2. Always `await` repository and service calls.
3. Use `await session.execute(select(...))` instead of `session.exec()`.
4. Use `result.scalar_one_or_none()` or `result.scalars().all()` to extract data.
5. CPU-bound tasks must be wrapped in `asyncio.to_thread`.
