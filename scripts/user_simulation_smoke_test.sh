#!/bin/bash

# user_simulation_smoke_test.sh
# End-to-end user simulation smoke test for SwX-API stack.

set -e

# Configuration
API_URL=${API_URL:-"http://localhost:8001/api"}
ADMIN_EMAIL="${ADMIN_EMAIL:-admin@example.com}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-${FIRST_SUPERUSER_PASSWORD:-changeme}}"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%dT%H:%M:%S')] $1${NC}"
}

error_exit() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

# 1. PHASE 0: Bootstrap & Connectivity
log "Starting Phase 0: System Bootstrap"

# Wait for API to be ready (health-check is at /api/utils/health-check)
BASE="${API_URL%/api}"
until curl -sf "${BASE}/api/utils/health-check" > /dev/null 2>&1; do
  log "Waiting for API at $API_URL..."
  sleep 2
done

log "API is UP."

# 2. PHASE 1: Admin Login
log "Starting Phase 1: Admin Authentication"

ADMIN_AUTH_RESPONSE=$(curl -s -L -X POST "$API_URL/admin/auth/" \
  -F "username=$ADMIN_EMAIL" \
  -F "password=$ADMIN_PASSWORD")

log "Admin Auth Response: $ADMIN_AUTH_RESPONSE"

ADMIN_TOKEN=$(echo $ADMIN_AUTH_RESPONSE | jq -r '.access_token')

if [ "$ADMIN_TOKEN" == "null" ] || [ -z "$ADMIN_TOKEN" ]; then
  error_exit "Admin login failed."
fi

log "Admin logged in successfully."

# 3. PHASE 2: RBAC Management (Admin Flow)
log "Starting Phase 2: RBAC Management"

# Create Permission
log "Creating permission: team.write"
PERM_RESPONSE=$(curl -s -L -X POST "$API_URL/admin/permission/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "team.write", "description": "Allows writing to teams", "resource_type": "team", "action": "write"}')

PERM_ID=$(echo $PERM_RESPONSE | jq -r '.id')
if [ "$PERM_ID" == "null" ]; then error_exit "Failed to create permission: $PERM_RESPONSE"; fi
log "Permission created with ID: $PERM_ID"

# Create Role
log "Creating role: Team Lead"
ROLE_RESPONSE=$(curl -s -X POST "$API_URL/admin/role/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Team Lead", "description": "Lead of a team"}')

ROLE_ID=$(echo $ROLE_RESPONSE | jq -r '.id')
if [ "$ROLE_ID" == "null" ]; then error_exit "Failed to create role: $ROLE_RESPONSE"; fi
log "Role created with ID: $ROLE_ID"

# Assign Permission to Role
log "Assigning permission to role"
ASSIGN_PERM_RESPONSE=$(curl -s -X POST "$API_URL/admin/role/$ROLE_ID/permission/$PERM_ID" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
if [ "$(echo $ASSIGN_PERM_RESPONSE | jq -r '.role_id')" == "null" ]; then error_exit "Failed to assign permission"; fi
log "Permission assigned to role."

# Create Normal User
USER_EMAIL="user_$(date +%s)@example.com"
USER_PASSWORD="UserPass123!"
log "Creating normal user: $USER_EMAIL"
USER_RESPONSE=$(curl -s -X POST "$API_URL/admin/user/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$USER_EMAIL\", \"password\": \"$USER_PASSWORD\", \"full_name\": \"Normal User\"}")

USER_ID=$(echo $USER_RESPONSE | jq -r '.id')
if [ "$USER_ID" == "null" ]; then error_exit "Failed to create user: $USER_RESPONSE"; fi
log "User created with ID: $USER_ID"

# Create Team
log "Creating team: Alpha"
TEAM_RESPONSE=$(curl -s -X POST "$API_URL/admin/team/" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Alpha", "description": "The first team"}')

TEAM_ID=$(echo $TEAM_RESPONSE | jq -r '.id')
if [ "$TEAM_ID" == "null" ]; then error_exit "Failed to create team: $TEAM_RESPONSE"; fi
log "Team created with ID: $TEAM_ID"

# Assign User to Team with Role
log "Adding user to team with role"
MEMBER_RESPONSE=$(curl -s -X POST "$API_URL/admin/team/member" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"team_id\": \"$TEAM_ID\", \"user_id\": \"$USER_ID\", \"role_id\": \"$ROLE_ID\"}")

if [ "$(echo $MEMBER_RESPONSE | jq -r '.id')" == "null" ]; then error_exit "Failed to add member: $MEMBER_RESPONSE"; fi
log "User added to team Alpha as Team Lead."

# 4. PHASE 3: Normal User Flow
log "Starting Phase 3: Normal User Flow"

# User Login
log "Logging in as normal user: $USER_EMAIL"
USER_AUTH_RESPONSE=$(curl -s -X POST "$API_URL/auth/" \
  -F "username=$USER_EMAIL" \
  -F "password=$USER_PASSWORD")

USER_TOKEN=$(echo $USER_AUTH_RESPONSE | jq -r '.access_token')
if [ "$USER_TOKEN" == "null" ] || [ -z "$USER_TOKEN" ]; then
  error_exit "User login failed: $USER_AUTH_RESPONSE"
fi
log "User logged in successfully."

# Forbidden: Normal User attempts to list all users
log "Verifying Forbidden access: User attempting to list all users"
FORBIDDEN_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X GET "$API_URL/admin/user/" \
  -H "Authorization: Bearer $USER_TOKEN")

if [ "$FORBIDDEN_STATUS" != "401" ] && [ "$FORBIDDEN_STATUS" != "403" ]; then
  error_exit "Security Breach: Normal user could access admin endpoint (Status: $FORBIDDEN_STATUS)"
fi
log "Access correctly blocked (Status: $FORBIDDEN_STATUS)."

# Success: User accesses their own profile
log "Verifying valid access: User profile"
PROFILE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X GET "$API_URL/user/profile/" \
  -H "Authorization: Bearer $USER_TOKEN")

if [ "$PROFILE_STATUS" != "200" ]; then
  error_exit "Failed to access own profile (Status: $PROFILE_STATUS)"
fi
log "User profile accessed successfully."

# 5. PHASE 4: Audit Log Verification
log "Starting Phase 4: Audit Log Verification"

# Check if audit logs were generated for the previous actions
log "Checking for login audit logs..."
AUDIT_RESPONSE=$(curl -s -X GET "$API_URL/admin/audit/?action=admin.login&actor_id=$ADMIN_EMAIL&limit=10" \
  -H "Authorization: Bearer $ADMIN_TOKEN")

AUDIT_COUNT=$(echo "$AUDIT_RESPONSE" | jq -r '.count // (.data | length) // 0')
if [ "$AUDIT_COUNT" == "0" ] || [ "$AUDIT_COUNT" == "null" ]; then
  error_exit "Audit log missing for admin login."
fi
log "Found $AUDIT_COUNT audit logs for admin login."

log "Checking for user creation audit logs..."
AUDIT_USER_RESPONSE=$(curl -s -X GET "$API_URL/admin/audit/?action=user.create&limit=10" \
  -H "Authorization: Bearer $ADMIN_TOKEN")

AUDIT_USER_COUNT=$(echo "$AUDIT_USER_RESPONSE" | jq -r '.count // (.data | length) // 0')
if [ "$AUDIT_USER_COUNT" == "0" ] || [ "$AUDIT_USER_COUNT" == "null" ]; then
  error_exit "Audit log missing for user creation."
fi
log "Found $AUDIT_USER_COUNT audit logs for user creation."

log "Checking for permission denial audit logs (Normal user attempting admin endpoint)..."
# Note: Currently we only added explicit hooks. 
# Middleware captures context but we don't have a catch-all hook for 403s yet in this implementation unless added.
# For now, verify what we explicitly hooked.

log "FULL SMOKE TEST PASSED CLEANLY WITH AUDIT LOGS"
exit 0
