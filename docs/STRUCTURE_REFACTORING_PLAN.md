# Structure Refactoring Plan

**Date:** 2024  
**Status:** In Progress

---

## Objective

Refactor the codebase from:
- `swx_api/core/` → `swx_core/` (reusable framework)
- `swx_api/app/` → `swx_app/` (minimal usage example)

---

## Steps

### 1. Create New Directory Structure
- Create `swx_core/` directory
- Create `swx_app/` directory

### 2. Move Framework Code
- Move `swx_api/core/` → `swx_core/`
- Update all internal imports from `swx_api.core.*` → `swx_core.*`

### 3. Move Application Code
- Move `swx_api/app/` → `swx_app/`
- Update all imports from `swx_api.app.*` → `swx_app.*`
- Update imports from `swx_api.core.*` → `swx_core.*`

### 4. Update Configuration Files
- `pyproject.toml` - Update package name and entry points
- `alembic.ini` - No changes needed (uses relative paths)
- `migrations/env.py` - Update imports
- `swx_core/cli/commands/make.py` - Update scaffolding paths

### 5. Update Dynamic Loaders
- `swx_core/router.py` - Update paths for route loading
- `swx_core/utils/loader.py` - Update module paths
- `swx_core/utils/model.py` - Update model paths

### 6. Update Entry Points
- `swx_core/main.py` - Update imports
- `swx_core/cli/main.py` - Update CLI entry point

### 7. Cleanup
- Remove old `swx_api/` directory
- Update documentation

---

## Import Mapping

| Old Import | New Import |
|------------|------------|
| `swx_api.core.*` | `swx_core.*` |
| `swx_api.app.*` | `swx_app.*` |

---

## Files Requiring Updates

### Configuration
- `pyproject.toml`
- `migrations/env.py`
- `alembic.ini` (may not need changes)

### Core Framework Files
- All files in `swx_core/` (internal imports)
- `swx_core/router.py` (route loading paths)
- `swx_core/utils/loader.py` (module loading paths)
- `swx_core/utils/model.py` (model loading paths)
- `swx_core/cli/commands/make.py` (scaffolding paths)

### Application Files
- All files in `swx_app/` (imports from core)

---

## Verification Checklist

- [ ] All imports updated
- [ ] Router loads routes correctly
- [ ] Models load correctly
- [ ] CLI works
- [ ] Migrations work
- [ ] Tests pass (if applicable)
- [ ] Documentation updated
