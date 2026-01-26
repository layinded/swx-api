# Policy Engine - Folder Structure Compliance ✅

**Date:** 2026-01-25  
**Status:** Complete - All files follow project structure conventions

---

## ✅ Folder Structure Compliance

All Policy Engine files are organized according to the project's established patterns:

### Architecture Pattern

```
Route → Controller → Service → Repository → Model
```

---

## File Organization

### 1. Models Layer
**Location:** `swx_core/models/`

- ✅ `policy.py` - Policy database model (SQLModel)
  - `Policy` - Main model
  - `PolicyEffect` - Enum (ALLOW, DENY, CONDITIONAL_ALLOW)
  - `ConditionOperator` - Enum (eq, ne, in, contains, etc.)
  - `Condition` - Pydantic model for conditions
  - `PolicyDecision` - Enum (ALLOW, DENY)
  - `PolicyEvaluation` - Pydantic model for evaluation results

### 2. Repository Layer
**Location:** `swx_core/repositories/`

- ✅ `policy_repository.py` - Database operations
  - `get_policy_by_id()` - Get by policy_id
  - `list_policies()` - List with pagination
  - `create_policy()` - Create new policy
  - `update_policy()` - Update existing policy
  - `delete_policy()` - Delete policy
  - `policy_exists()` - Check existence

### 3. Service Layer
**Location:** `swx_core/services/`

- ✅ `policy_service.py` - Business logic for Policy CRUD
  - `list_policies_service()` - List database policies
  - `list_system_policies_service()` - List system policies
  - `get_policy_service()` - Get policy (checks both DB and system)
  - `create_policy_service()` - Create with validation
  - `update_policy_service()` - Update with system policy check
  - `delete_policy_service()` - Delete with system policy check

- ✅ `policy/` - Policy Engine core (subdirectory)
  - `__init__.py` - Module exports
  - `actor.py` - Actor model for evaluation
  - `resource.py` - Resource model for evaluation
  - `context.py` - Context model for evaluation
  - `policy_engine.py` - Core evaluation engine
  - `policy_registry.py` - System policy registry
  - `dependencies.py` - FastAPI dependency (`require_policy()`)

### 4. Controller Layer
**Location:** `swx_core/controllers/`

- ✅ `policy_controller.py` - Request handling
  - `list_policies_controller()` - List database policies
  - `list_system_policies_controller()` - List system policies
  - `get_policy_controller()` - Get by ID
  - `create_policy_controller()` - Create new
  - `update_policy_controller()` - Update existing
  - `delete_policy_controller()` - Delete

### 5. Route Layer
**Location:** `swx_core/routes/admin/`

- ✅ `policy_route.py` - API endpoints
  - `GET /api/admin/policy/` - List database policies
  - `GET /api/admin/policy/system` - List system policies
  - `GET /api/admin/policy/{policy_id}` - Get policy
  - `POST /api/admin/policy/` - Create policy
  - `PATCH /api/admin/policy/{policy_id}` - Update policy
  - `DELETE /api/admin/policy/{policy_id}` - Delete policy

---

## Module Exports

### `swx_core/repositories/__init__.py`
```python
from swx_core.repositories import policy_repository
```

### `swx_core/services/__init__.py`
```python
from swx_core.services import policy_service
```

### `swx_core/controllers/__init__.py`
```python
from swx_core.controllers import policy_controller
```

### `swx_core/services/policy/__init__.py`
```python
from swx_core.services.policy.policy_engine import PolicyEngine, PolicyDecision
from swx_core.services.policy.actor import Actor, ActorType
from swx_core.services.policy.resource import Resource
from swx_core.services.policy.context import PolicyContext
from swx_core.services.policy.policy_registry import PolicyRegistry, register_system_policies
from swx_core.services.policy.dependencies import require_policy
```

---

## Import Patterns

### In Routes
```python
from swx_core.controllers import policy_controller
```

### In Controllers
```python
from swx_core.services import policy_service
```

### In Services
```python
from swx_core.repositories import policy_repository
```

### In Repositories
```python
from swx_core.models.policy import Policy
```

---

## Structure Comparison

### Other Modules (e.g., Team)
```
swx_core/
├── models/team.py
├── repositories/team_repository.py
├── services/team_service.py
├── controllers/team_controller.py
└── routes/admin/team_route.py
```

### Policy Module (Same Pattern)
```
swx_core/
├── models/policy.py
├── repositories/policy_repository.py
├── services/policy_service.py
├── services/policy/          # Policy Engine core
│   ├── actor.py
│   ├── resource.py
│   ├── context.py
│   ├── policy_engine.py
│   ├── policy_registry.py
│   └── dependencies.py
├── controllers/policy_controller.py
└── routes/admin/policy_route.py
```

---

## ✅ Compliance Checklist

- ✅ Models in `swx_core/models/`
- ✅ Repositories in `swx_core/repositories/`
- ✅ Services in `swx_core/services/`
- ✅ Controllers in `swx_core/controllers/`
- ✅ Routes in `swx_core/routes/admin/`
- ✅ Module exports in `__init__.py` files
- ✅ Import patterns match project conventions
- ✅ Follows Route → Controller → Service → Repository → Model pattern
- ✅ Audit logging integrated in routes
- ✅ Error handling consistent with other modules

---

## Summary

All Policy Engine files are correctly organized according to the project's established folder structure and architectural patterns. The implementation follows the same conventions as other modules (Team, Role, Permission, etc.), ensuring consistency and maintainability.
