# User Simulation Plan

This document defines the user personas and their journeys for the end-to-end smoke tests of the SwX-API stack.

## 1. User Personas

### A. System Operator
- **Context**: The "root" user of the system.
- **Credentials**: Uses system-level credentials (e.g., environment variables or bootstrap token).
- **Role**: Bootstraps the system from zero.
- **Actions**:
    - Runs database migrations.
    - Creates initial permissions.
    - Creates initial admin roles.
    - Creates the first System Admin user.
    - Ensures the system is ready for the Admin User.

### B. Admin User
- **Context**: An elevated user with full management rights over the RBAC system.
- **Credentials**: JWT obtained via login.
- **Role**: Manages the organizational structure and access control.
- **Actions**:
    - Manages Permissions (CRUD).
    - Manages Roles (CRUD).
    - Links Permissions to Roles.
    - Manages Users (CRUD).
    - Assigns Roles to Users.
    - Manages Teams (CRUD).
    - Assigns Users to Teams with specific Team Roles.
- **Constraints**: Should not be performing normal business operations (e.g., creating products).

### C. Normal User
- **Context**: A standard user belonging to one or more teams.
- **Credentials**: JWT obtained via login or registration.
- **Role**: Performs day-to-day operations within the scope of their assigned permissions.
- **Actions**:
    - Accesses their own profile.
    - Views team-specific resources.
    - Performs actions allowed by their role (e.g., viewing data).
    - Attempts forbidden actions (e.g., accessing admin routes) to verify blocking.
- **Constraints**: Cannot escalate privileges or access data of other teams.

## 2. User Journeys

### Journey 1: System Bootstrap (System Operator)
1. Start Stack.
2. Run Migrations.
3. Call Bootstrap API (or use CLI) to:
    - Create `admin` and `user` base roles.
    - Create `system.manage` and `user.view` permissions.
    - Create a `superuser@example.com` with `is_superuser=True`.
4. Verify idempotency by running again.

### Journey 2: RBAC Management (Admin User)
1. Login as Admin.
2. Create a new permission `team.write`.
3. Create a new role `Team Lead`.
4. Assign `team.write` and `user.view` to `Team Lead`.
5. Create a Normal User.
6. Create a Team "Alpha".
7. Assign Normal User to Team "Alpha" with role `Team Lead`.

### Journey 3: Normal Operation & Enforcement (Normal User)
1. Login as Normal User.
2. Verify access to Team "Alpha" resources.
3. Verify access to `team.write` protected actions.
4. Attempt to list all users (Admin only) - Expect 403.
5. Attempt to access Team "Beta" resources - Expect 403.
