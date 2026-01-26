# Policy Engine Integration Examples

This document shows how to integrate the Policy Engine into routes, replacing manual ownership checks and permission spaghetti.

---

## Before: Manual Ownership Check

**❌ BAD: Ownership check in route**

```python
@router.get("/{user_id}", response_model=UserPublic)
async def read_user_by_id(
    user_id: UUID,
    session: SessionDep,
    current_user: UserDep,
    request: Request,
) -> Any:
    # Manual ownership check - BAD!
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="access_denied")
    return await get_user_by_id_service(session, str(user_id), current_user, request)
```

**Problems:**
- Ownership logic scattered across routes
- Easy to forget checks
- Inconsistent error messages
- Not auditable
- Hard to test

---

## After: Policy-Based Authorization

**✅ GOOD: Policy evaluation**

```python
from swx_core.services.policy.dependencies import require_policy

@router.get("/{user_id}", response_model=UserPublic)
async def read_user_by_id(
    user_id: UUID,
    session: SessionDep,
    current_user: UserDep,
    request: Request,
    _policy: None = Depends(require_policy(
        action="user:read",
        resource_type="user",
        resource_id=user_id,
        resource_owner_id=user_id  # User is owner of themselves
    ))
) -> Any:
    # Policy already evaluated - proceed
    return await get_user_by_id_service(session, str(user_id), current_user, request)
```

**Benefits:**
- Centralized authorization logic
- Consistent error handling
- Full audit trail
- Easy to test
- Policies are explicit and auditable

---

## Example: Team Update with Policy

**Before:**
```python
@router.patch("/{team_id}", response_model=TeamPublic)
async def update_team(
    session: SessionDep,
    team_id: UUID,
    team_in: TeamUpdate,
    current_admin: AdminUserDep,
    request: Request,
) -> Any:
    # No ownership check - admin can update any team
    # This is a security risk!
    team = await team_controller.update_team_controller(session, team_id, team_in)
    return team
```

**After:**
```python
from swx_core.services.policy.dependencies import require_policy
from swx_core.repositories.team_repository import get_team_by_id

@router.patch("/{team_id}", response_model=TeamPublic)
async def update_team(
    session: SessionDep,
    team_id: UUID,
    team_in: TeamUpdate,
    current_user: UserDep,  # Changed from admin - now users can update their teams
    request: Request,
    _policy: None = Depends(require_policy(
        action="team:update",
        resource_type="team",
        resource_id=team_id
    ))
) -> Any:
    # Policy ensures:
    # 1. User has "team.owner" role in the team
    # 2. User's team_id matches resource.team_id
    # All checked automatically!
    team = await team_controller.update_team_controller(session, team_id, team_in)
    return team
```

**Policy that enables this:**
```python
{
    "policy_id": "team.update.owner",
    "effect": "allow",
    "action_pattern": "team:update",
    "resource_type": "team",
    "conditions": [
        {
            "attribute": "actor.team_id",
            "operator": "eq",
            "value": "resource.team_id"
        },
        {
            "attribute": "actor.roles",
            "operator": "contains",
            "value": "team.owner"
        }
    ]
}
```

---

## Example: Resource Loading for Policy

Sometimes you need to load the resource first to get its attributes:

```python
from swx_core.repositories.team_repository import get_team_by_id
from swx_core.repositories.user_repository import get_user_by_id

@router.patch("/{team_id}", response_model=TeamPublic)
async def update_team(
    session: SessionDep,
    team_id: UUID,
    team_in: TeamUpdate,
    current_user: UserDep,
    request: Request,
) -> Any:
    # Load resource to get attributes for policy evaluation
    team = await get_team_by_id(session, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Get team owner from team members (if teams have owners)
    # For now, policy will check team membership via actor.team_id
    
    # Evaluate policy
    from swx_core.services.policy import PolicyEngine, Actor, Resource, PolicyContext
    from swx_core.services.policy.actor import ActorType
    from swx_core.rbac.helpers import get_user_roles, get_user_permissions
    from datetime import datetime
    
    roles = await get_user_roles(session, current_user.id, team_id=team_id, domain="user")
    permissions = await get_user_permissions(session, current_user.id, team_id=team_id, domain="user")
    
    actor = Actor(
        id=current_user.id,
        type=ActorType.USER,
        roles=[r.name for r in roles],
        permissions=[p.name for p in permissions],
        team_id=team_id,
        is_superuser=current_user.is_superuser,
        attributes={"email": current_user.email}
    )
    
    resource = Resource(
        type="team",
        id=team.id,
        team_id=team.id,
        attributes={}
    )
    
    context = PolicyContext(
        timestamp=datetime.utcnow(),
        ip_address=request.client.host if request.client else None,
        environment="local",
        request_id=request.headers.get("x-request-id", "")
    )
    
    engine = PolicyEngine(session)
    result = await engine.evaluate(actor, "team:update", resource, context)
    
    if result.decision.value == "deny":
        raise HTTPException(
            status_code=403,
            detail=f"Access denied: {result.reason}"
        )
    
    # Policy passed - proceed
    return await team_controller.update_team_controller(session, team_id, team_in)
```

**Better: Use the dependency helper**

The `require_policy()` dependency handles all this automatically. You just need to provide resource information:

```python
@router.patch("/{team_id}", response_model=TeamPublic)
async def update_team(
    session: SessionDep,
    team_id: UUID,
    team_in: TeamUpdate,
    current_user: UserDep,
    request: Request,
    _policy: None = Depends(require_policy(
        action="team:update",
        resource_type="team",
        resource_id=team_id,
        resource_team_id=team_id  # Policy will check actor.team_id == resource.team_id
    ))
) -> Any:
    # Policy already evaluated - proceed
    return await team_controller.update_team_controller(session, team_id, team_in)
```

---

## Example: Billing-Gated Feature

```python
from swx_core.services.policy.dependencies import require_policy
from swx_core.services.billing.entitlement_resolver import EntitlementResolver
from swx_core.models.billing import BillingAccountType

@router.get("/analytics/advanced")
async def get_advanced_analytics(
    session: SessionDep,
    current_user: UserDep,
    request: Request,
    _policy: None = Depends(require_policy(
        action="analytics:read:advanced",
        resource_type="analytics",
        resource_attributes={
            "feature": "advanced.analytics"
        }
    ))
) -> Any:
    # Policy checks:
    # 1. User has "advanced.analytics" entitlement
    # 2. Subscription is active
    # All handled by policy!
    return {"analytics": "..."}
```

**Policy:**
```python
{
    "policy_id": "analytics.advanced.entitlement",
    "effect": "conditional",
    "action_pattern": "analytics:read:advanced",
    "resource_type": "analytics",
    "conditions": [
        {
            "attribute": "actor.attributes.subscription_status",
            "operator": "eq",
            "value": "active"
        },
        {
            "attribute": "actor.attributes.entitlements",
            "operator": "contains",
            "value": "advanced.analytics"
        }
    ]
}
```

---

## Migration Guide

### Step 1: Identify Manual Checks

Find routes with manual ownership/permission checks:

```bash
grep -r "if.*\.id.*!=" swx_core/routes/
grep -r "HTTPException.*403" swx_core/routes/
```

### Step 2: Replace with Policy

1. Add `require_policy()` dependency
2. Remove manual checks
3. Ensure resource attributes are provided

### Step 3: Create Policies

1. Define policy in `policy_registry.py` or database
2. Test policy evaluation
3. Verify audit logs

### Step 4: Remove Dead Code

After migration, remove:
- Manual ownership checks
- Inline permission logic
- Ad-hoc authorization code

---

## Best Practices

1. **Always use `require_policy()`** - Never bypass policy evaluation
2. **Load resources first** - If policy needs resource attributes, load them
3. **Provide complete context** - Include all relevant resource attributes
4. **Test policies** - Write tests for policy evaluation
5. **Audit everything** - All policy decisions are logged automatically
6. **Fail closed** - Default to DENY if no policy matches

---

## Common Patterns

### Pattern 1: Self-Service (Own Resource)

```python
_policy: None = Depends(require_policy(
    action="user:update",
    resource_type="user",
    resource_id=user_id,
    resource_owner_id=user_id  # User owns themselves
))
```

### Pattern 2: Team Scoped

```python
_policy: None = Depends(require_policy(
    action="team:update",
    resource_type="team",
    resource_id=team_id,
    resource_team_id=team_id  # Policy checks actor.team_id == resource.team_id
))
```

### Pattern 3: Admin Only

```python
# Admin routes already have AdminUserDep
# Policy can check actor.type == "admin"
_policy: None = Depends(require_policy(
    action="admin:audit:read",
    resource_type="audit"
))
```

### Pattern 4: Billing Gated

```python
_policy: None = Depends(require_policy(
    action="feature:advanced_analytics",
    resource_type="feature",
    resource_attributes={
        "feature_key": "advanced.analytics"
    }
))
```

---

## Testing Policies

```python
import pytest
from swx_core.services.policy import PolicyEngine, Actor, Resource, PolicyContext
from swx_core.services.policy.actor import ActorType

async def test_team_update_policy(session):
    actor = Actor(
        id=user_id,
        type=ActorType.USER,
        roles=["team.owner"],
        team_id=team_id
    )
    resource = Resource(
        type="team",
        id=team_id,
        team_id=team_id
    )
    context = PolicyContext(timestamp=datetime.utcnow())
    
    engine = PolicyEngine(session)
    result = await engine.evaluate(actor, "team:update", resource, context)
    
    assert result.decision.value == "allow"
```

---

## Success Checklist

- [ ] No `if current_user.id != resource_id` checks in routes
- [ ] No manual permission checks in routes
- [ ] All routes use `require_policy()`
- [ ] Policies are defined in registry or database
- [ ] Policy decisions are audited
- [ ] Tests cover policy evaluation
- [ ] Documentation explains policies
