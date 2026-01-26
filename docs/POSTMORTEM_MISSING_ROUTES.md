### Post-Mortem: Missing `swx_app` Routes & Admin Authentication Issues

#### 1. Root Cause Analysis

**A. Misregistered `swx_app` Routes**
- **Issue**: Routes in `swx_app/` were being registered with incorrect module paths (e.g., `swx_app.routes.swx_app.routes.qa_article_route`).
- **Cause**: The `load_user_routes` and `load_versioned_routes` functions in `swx_core/router.py` were manually prepending the `swx_app.routes` prefix to module names already returned by `dynamic_import`. Since `dynamic_import` was configured to return full module paths, this resulted in double-prefixing, causing `FastAPI` to fail to find the modules or register them incorrectly.

**B. Admin Authentication Failure**
- **Issue**: `scripts/user_simulation_smoke_test.sh` failed during Phase 1 (Admin Login) after a clean boot.
- **Cause 1**: Naming inconsistency in `AdminUser` model. The database field was `createdAt` (camelCase) while the rest of the project uses `created_at` (snake_case). This caused 500 errors when retrieving the admin user.
- **Cause 2**: Idempotency issues in `db_setup.py`. The initialization script created the admin user but did not update the password if the user already existed. In some environments, a stale hash or different default password in the DB caused authentication failures.
- **Cause 3**: Smoke test configuration. The script was pointing to `localhost:8000` (container internal port) instead of `localhost:8001` (host mapped port), and it used a mismatched password.

#### 2. Fixes Implemented

- **Router Logic**: Updated `swx_core/router.py` to use the full module names provided by `dynamic_import` without redundant prefixing.
- **Model Standardization**: Renamed `createdAt` to `created_at` in `AdminUser` model and updated migrations.
- **Bootstrap Idempotency**: Enhanced `init_superuser` in `swx_core/database/db_setup.py` to ensure the Admin superuser is always present and has the correct password from `settings.py`.
- **Smoke Test Robustness**: 
    - Corrected the `API_URL` to use port `8001`.
    - Aligned credentials with `settings.py`.
    - Updated endpoint paths (e.g., `/api/user/profile/` instead of `/api/user/me`).
    - Added mandatory fields for RBAC resource creation.

#### 3. Prevention & Guards

- **Explicit Loading**: The framework now logs exactly which routes are registered and at what paths during startup.
- **Automated Verification**: The `user_simulation_smoke_test.sh` is now integrated into the development workflow to catch registration and RBAC regressions early.
- **Model Linting**: naming conventions are now strictly snake_case across all core models.
