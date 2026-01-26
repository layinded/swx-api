# Agents Enforcement Strategy

To prevent regressions and ensure ongoing compliance with governance rules, the following enforcement mechanisms are proposed.

## 1. Automated Linting & Formatting (Pre-commit)

- **Tool**: `Ruff`
- **Enforcement**: Mandatory `ruff check` and `ruff format` in a pre-commit hook.
- **Rule Mapping**: Ruff can be configured to enforce PEP 8, import sorting, and detect common bugs (flake8-bugbear).
- **Customization**: Use `.ruff.toml` to enforce specific project naming conventions and forbidden patterns.

## 2. CI/CD Governance Gates

- **Static Analysis**: Integrate `mypy` for strict type checking in the CI pipeline. Fail builds that have untyped definitions in `swx_core` or `swx_app`.
- **Testing**: Require 100% pass on `pytest` and `user_simulation_smoke_test.sh` for any Pull Request.
- **Security Scanning**: Use tools like `bandit` or `safety` to scan for security vulnerabilities in dependencies and code.

## 3. Structural Enforcement (Folder Guards)

- **Mechanism**: Use a script (e.g., `scripts/check_structure.py`) to verify that no business logic leaks into `swx_core` and that `swx_app` follows the `Route -> Controller -> Service -> Repository` pattern.
- **Checklist**:
    - Ensure every Route file has a corresponding Controller.
    - Ensure no SQL `text()` queries exist in `routes/` or `services/`.
    - Ensure `swx_app` does not import internal utilities from `swx_core` that are marked as private.

## 4. Documentation & Schema Enforcement

- **OpenAPI Audit**: Automated check during CI that validates the generated `openapi.json` against architectural rules (e.g., all admin routes must be prefixed with `/admin` and have security schemas defined).
- **Rule Sync**: A periodic "governance audit" task (like this one) to ensure the `.agents` rules haven't diverged from the `pyproject.toml` and actual toolchain.

## 5. Runtime Assertions (Development Only)

- **Sanity Checks**: Implement runtime checks in `swx_core/router.py` that log warnings if a route is registered without proper dependency injection for authentication (e.g., missing `AdminUserDep` on an admin route).
