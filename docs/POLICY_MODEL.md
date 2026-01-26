# Policy Model Design (ABAC)

**Version:** 1.0  
**Date:** 2026-01-25  
**Author:** Staff Security Engineer + Authorization Architect

---

## Overview

This document defines the Attribute-Based Access Control (ABAC) policy model that sits on top of RBAC and billing entitlements. The policy engine provides the final authorization layer, answering "under which conditions" access is granted.

**Key Principle:** Policies are explicit, auditable, and deterministic. They evaluate conditions but contain no business logic.

---

## Architecture Layers

```
┌─────────────────────────────────────┐
│   Policy Engine (ABAC)              │  ← Final authorization layer
│   "Under which conditions?"         │
├─────────────────────────────────────┤
│   Billing Entitlements               │  ← "What features?"
├─────────────────────────────────────┤
│   RBAC (Permissions & Roles)         │  ← "Who has what?"
├─────────────────────────────────────┤
│   Authentication                     │  ← "Who are you?"
└─────────────────────────────────────┘
```

**Evaluation Order:**
1. Authentication: Verify identity
2. RBAC: Check if user has required permission
3. Entitlements: Check if feature is available on plan
4. **Policy: Check if conditions are met**

---

## Policy Structure

### Core Components

A policy evaluates four dimensions:

1. **Actor** - Who is making the request
2. **Action** - What action is being attempted
3. **Resource** - What resource is being accessed
4. **Context** - Environmental conditions

### Policy Definition

```python
class Policy:
    id: str                    # Unique identifier (e.g., "team.update.owner")
    name: str                  # Human-readable name
    description: str           # Policy purpose
    effect: PolicyEffect       # ALLOW | DENY | CONDITIONAL_ALLOW
    conditions: List[Condition] # Evaluation conditions
    priority: int              # Higher priority = evaluated first
    enabled: bool              # Can be disabled without deletion
```

### Policy Effect

```python
class PolicyEffect(str, Enum):
    ALLOW = "allow"                    # Explicitly allow
    DENY = "deny"                      # Explicitly deny (highest priority)
    CONDITIONAL_ALLOW = "conditional"  # Allow if conditions met
```

**Evaluation Rules:**
- `DENY` policies always take precedence
- `ALLOW` policies grant access if conditions pass
- `CONDITIONAL_ALLOW` requires all conditions to be true
- If no policy matches, **fail closed** (DENY)

---

## Actor Model

The actor represents the entity making the request.

```python
class Actor:
    id: UUID                    # User/Admin/System ID
    type: ActorType             # USER | ADMIN | SYSTEM
    roles: List[str]            # Role names (from RBAC)
    permissions: List[str]      # Permission names (from RBAC)
    attributes: Dict[str, Any]  # Additional attributes
    team_id: Optional[UUID]     # Current team context
    is_superuser: bool          # Superuser flag
```

**Actor Types:**
- `USER` - Regular application user
- `ADMIN` - Admin domain user
- `SYSTEM` - Internal system/service account

**Actor Attributes:**
- `email` - User email
- `is_active` - Account status
- `subscription_status` - Billing subscription status
- `ip_address` - Request origin IP
- `user_agent` - Client user agent
- Custom attributes as needed

---

## Action Model

Actions are string identifiers representing operations.

**Format:** `{resource_type}:{operation}`

**Examples:**
- `team:update`
- `user:delete`
- `billing:upgrade`
- `article:publish`
- `admin:audit:read`

**Conventions:**
- Use lowercase with colons as separators
- Resource type comes first
- Operation follows
- Nested actions use multiple colons

---

## Resource Model

Resources represent the entities being accessed.

```python
class Resource:
    type: str                   # Resource type (e.g., "team", "user", "article")
    id: Optional[UUID]          # Resource ID (None for collection operations)
    attributes: Dict[str, Any]  # Resource attributes
    owner_id: Optional[UUID]    # Resource owner
    team_id: Optional[UUID]     # Associated team
```

**Resource Types:**
- `team` - Team resources
- `user` - User resources
- `article` - Article/content resources
- `billing` - Billing resources
- `audit` - Audit log resources
- Custom resource types

**Resource Attributes:**
- `status` - Resource status
- `visibility` - Public/private/team
- `created_at` - Creation timestamp
- Custom attributes per resource type

---

## Context Model

Context represents environmental and request-specific conditions.

```python
class PolicyContext:
    timestamp: datetime          # Request timestamp
    ip_address: Optional[str]   # Client IP address
    user_agent: Optional[str]   # Client user agent
    environment: str             # "local" | "staging" | "production"
    tenant_id: Optional[UUID]   # Multi-tenant context
    request_id: str              # Request correlation ID
    metadata: Dict[str, Any]    # Additional context
```

**Context Usage:**
- Time-based policies (e.g., "only during business hours")
- IP-based restrictions
- Environment-specific rules
- Multi-tenant isolation

---

## Condition Model

Conditions are boolean expressions that evaluate to true/false.

```python
class Condition:
    attribute: str              # Attribute path (e.g., "actor.team_id")
    operator: ConditionOperator  # Comparison operator
    value: Any                   # Comparison value
    logical_op: Optional[str]    # AND | OR (for compound conditions)
```

### Condition Operators

```python
class ConditionOperator(str, Enum):
    EQUALS = "eq"                # actor.team_id == resource.team_id
    NOT_EQUALS = "ne"            # actor.id != resource.owner_id
    IN = "in"                    # actor.role in ["admin", "editor"]
    NOT_IN = "not_in"            # actor.ip_address not in blocked_ips
    GREATER_THAN = "gt"          # resource.size > 1000
    LESS_THAN = "lt"             # resource.size < 10000
    CONTAINS = "contains"        # actor.permissions contains "user:write"
    STARTS_WITH = "starts_with"  # resource.type starts_with "team"
    EXISTS = "exists"            # actor.subscription_status exists
    NOT_EXISTS = "not_exists"    # resource.deleted_at not_exists
```

### Attribute Paths

Conditions reference attributes using dot notation:

**Actor Attributes:**
- `actor.id` - Actor UUID
- `actor.type` - Actor type (USER/ADMIN/SYSTEM)
- `actor.team_id` - Current team context
- `actor.roles` - List of role names
- `actor.permissions` - List of permission names
- `actor.is_superuser` - Superuser flag
- `actor.attributes.email` - Email address
- `actor.attributes.subscription_status` - Billing status

**Resource Attributes:**
- `resource.id` - Resource UUID
- `resource.type` - Resource type
- `resource.owner_id` - Resource owner
- `resource.team_id` - Associated team
- `resource.attributes.status` - Resource status

**Context Attributes:**
- `context.timestamp` - Request timestamp
- `context.ip_address` - Client IP
- `context.environment` - Environment name
- `context.tenant_id` - Tenant ID

---

## Policy Examples

### Example 1: Team Owner Update

**Policy:** `team.update.owner`

```python
{
    "id": "team.update.owner",
    "name": "Team Owner Update",
    "description": "Only team owners can update team settings",
    "effect": "allow",
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
    ],
    "priority": 100
}
```

**Evaluation:**
- ✅ Actor is in the same team as the resource
- ✅ Actor has "team.owner" role
- **Result:** ALLOW

---

### Example 2: Business Hours Restriction

**Policy:** `admin.audit.read.business_hours`

```python
{
    "id": "admin.audit.read.business_hours",
    "name": "Business Hours Audit Access",
    "description": "Audit logs only accessible during business hours",
    "effect": "conditional",
    "conditions": [
        {
            "attribute": "context.timestamp.hour",
            "operator": "gte",
            "value": 9
        },
        {
            "attribute": "context.timestamp.hour",
            "operator": "lt",
            "value": 17
        },
        {
            "attribute": "context.timestamp.weekday",
            "operator": "lt",
            "value": 5  # Monday-Friday
        }
    ],
    "priority": 50
}
```

**Evaluation:**
- ✅ Current hour >= 9 (9 AM)
- ✅ Current hour < 17 (5 PM)
- ✅ Weekday < 5 (Monday-Friday)
- **Result:** ALLOW (if all conditions pass)

---

### Example 3: IP Whitelist

**Policy:** `admin.dangerous_action.ip_whitelist`

```python
{
    "id": "admin.dangerous_action.ip_whitelist",
    "name": "IP Whitelist for Dangerous Actions",
    "description": "Dangerous admin actions only from whitelisted IPs",
    "effect": "deny",
    "conditions": [
        {
            "attribute": "context.ip_address",
            "operator": "not_in",
            "value": ["10.0.0.0/8", "192.168.1.0/24"]
        }
    ],
    "priority": 200  # High priority (DENY policies)
}
```

**Evaluation:**
- ❌ IP not in whitelist
- **Result:** DENY (highest priority)

---

### Example 4: Resource Ownership

**Policy:** `user.update.own_resource`

```python
{
    "id": "user.update.own_resource",
    "name": "Update Own Resources",
    "description": "Users can update their own resources",
    "effect": "allow",
    "conditions": [
        {
            "attribute": "actor.id",
            "operator": "eq",
            "value": "resource.owner_id"
        }
    ],
    "priority": 100
}
```

**Evaluation:**
- ✅ Actor ID matches resource owner ID
- **Result:** ALLOW

---

### Example 5: Billing-Gated Feature

**Policy:** `feature.advanced_analytics.entitlement`

```python
{
    "id": "feature.advanced_analytics.entitlement",
    "name": "Advanced Analytics Entitlement",
    "description": "Requires advanced.analytics entitlement",
    "effect": "conditional",
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
    ],
    "priority": 75
}
```

**Evaluation:**
- ✅ Subscription is active
- ✅ User has "advanced.analytics" entitlement
- **Result:** ALLOW (if all conditions pass)

---

## Policy Evaluation Flow

```
1. Collect all policies for (action, resource_type)
2. Sort by priority (highest first)
3. For each policy:
   a. Check if policy is enabled
   b. Evaluate all conditions
   c. If DENY policy and conditions pass → DENY (immediate)
   d. If ALLOW policy and conditions pass → ALLOW (continue checking)
   e. If CONDITIONAL_ALLOW and conditions pass → ALLOW (continue checking)
4. If no policy matched → DENY (fail closed)
5. If multiple ALLOW policies matched → ALLOW (most permissive)
```

**Important:** DENY policies are evaluated first and take precedence.

---

## Policy Storage

Policies are stored in the database but can also be defined in code for system policies.

### Database Model

```python
class Policy(Base, table=True):
    id: str                      # Unique identifier
    name: str                    # Human-readable name
    description: str            # Policy description
    effect: PolicyEffect         # ALLOW | DENY | CONDITIONAL_ALLOW
    action_pattern: str          # Action pattern (supports wildcards)
    resource_type: str           # Resource type
    conditions: JSONB           # Condition definitions (JSON)
    priority: int                # Evaluation priority
    enabled: bool                # Is policy active
    created_at: datetime
    updated_at: datetime
```

### System Policies

System policies are defined in code and loaded at startup. They cannot be modified via API but can be disabled.

---

## Policy Registry

Policies are registered in a central registry with clear ownership.

**Registry Structure:**
- Policy ID → Policy Definition
- Action → List of Policy IDs
- Resource Type → List of Policy IDs

**Ownership:**
- Each policy has an `owner` field (module/team)
- Policies can be tagged for organization
- Clear documentation of policy purpose

---

## Audit & Compliance

### Policy Decision Logging

Every policy evaluation is logged:

```python
{
    "timestamp": "2026-01-25T20:00:00Z",
    "policy_id": "team.update.owner",
    "actor_id": "user-123",
    "action": "team:update",
    "resource_type": "team",
    "resource_id": "team-456",
    "decision": "ALLOW",
    "conditions_evaluated": [
        {"condition": "actor.team_id == resource.team_id", "result": true},
        {"condition": "actor.roles contains 'team.owner'", "result": true}
    ],
    "request_id": "req-789"
}
```

### Policy Violations

DENY decisions trigger:
1. Audit log entry (always)
2. Alert (if configured for sensitive actions)
3. Security event (if critical)

---

## Integration Points

### 1. Route Protection

```python
@router.put("/teams/{team_id}")
async def update_team(
    team_id: UUID,
    current_user: UserDep,
    require_policy("team:update", resource_type="team", resource_id=team_id)
):
    # Policy already evaluated - proceed
    ...
```

### 2. RBAC Integration

Policies check RBAC permissions as conditions:

```python
{
    "attribute": "actor.permissions",
    "operator": "contains",
    "value": "team:write"
}
```

### 3. Billing Integration

Policies check entitlements as conditions:

```python
{
    "attribute": "actor.attributes.entitlements",
    "operator": "contains",
    "value": "advanced.analytics"
}
```

---

## Success Criteria

✅ **No ownership checks in routes** - All ownership logic in policies  
✅ **No permission spaghetti** - Single policy evaluation point  
✅ **All authorization flows through policy engine** - No bypasses  
✅ **Policy decisions explainable** - Full audit trail  
✅ **Deterministic evaluation** - Same inputs = same output  
✅ **Fail closed** - Default to DENY if no policy matches  

---

## Next Steps

1. Implement Policy Engine Core (`policy_engine.py`)
2. Create Policy Registry (`policy_registry.py`)
3. Build integration helpers (`require_policy()`)
4. Add audit logging hooks
5. Create migration for Policy model
