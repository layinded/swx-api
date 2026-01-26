# Audit Log Scope

This document defines the scope of the industry-standard audit logging system for SwX-API.

## Security-Relevant Events

### Authentication
- **Login Success**: Captured when a user or admin successfully authenticates.
- **Login Failure**: Captured when an authentication attempt fails (e.g., wrong password, non-existent user). Includes actor identity if known.
- **Token Refresh**: Captured when a new access token is issued via a refresh token.
- **Logout**: Captured when a refresh token is revoked.
- **Password Reset Request**: Captured when a password recovery email is requested.
- **Password Reset Success**: Captured when a password is successfully reset.

### Authorization
- **Permission Denied**: Captured when a request is rejected due to insufficient permissions (403 Forbidden).
- **Unauthorized Access**: Captured when an unauthenticated request attempts to access a protected resource (401 Unauthorized).

## Business-Relevant Events

### Identity Lifecycle
- **User Creation**: Captured when a new user is registered or created by an admin.
- **User Updates**: Captured when user profile information is modified.
- **User Deactivation**: Captured when a user account is disabled or deleted.

### RBAC Lifecycle
- **Role Management**: Creation, update, and deletion of roles.
- **Permission Management**: Creation and deletion of permissions.
- **Role-Permission Assignment**: Granting or revoking permissions to/from roles.
- **User-Role Assignment**: Assigning or removing roles to/from users (global or scoped).

### Team Events
- **Team Management**: Creation, update, and deletion of teams.
- **Membership Changes**: Adding or removing users to/from teams.
- **Team Role Changes**: Updating a user's role within a team.

## System Events
- **Bootstrap Actions**: Initial system setup and superuser creation.
- **Database Migrations**: Execution of schema updates (logged as system actions).
- **Configuration Changes**: Significant changes to system settings (if manageable via API).

## Audit Log Attributes
Each audit log entry must capture:
- `id`: Unique identifier (UUID).
- `timestamp`: UTC time of the event.
- `actor_type`: Type of actor (system, admin, user).
- `actor_id`: Unique ID of the actor.
- `action`: Specific action performed (e.g., `user.create`, `auth.login`).
- `resource_type`: Type of resource affected (e.g., `user`, `role`, `team`).
- `resource_id`: ID of the affected resource.
- `outcome`: Result of the action (success or failure).
- `ip_address`: IP address of the requester.
- `user_agent`: User agent string of the requester.
- `request_id`: Unique ID for tracing the specific request.
- `metadata`: Structured JSON containing additional context (excluding sensitive data).
