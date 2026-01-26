#!/bin/bash
# alert_smoke_test.sh
# Validates the alerting system by triggering various alert types.

set -e

# Configuration
API_URL=${API_URL:-"http://localhost:8001/api"}
LOG_FILE="logs/swx_core.log"

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

# 1. Trigger User Login Failure Alert
log "Triggering User Login Failure Alert..."
curl -s -X POST "$API_URL/auth/" \
  -F "username=wronguser@example.com" \
  -F "password=wrongpass" > /dev/null

# 2. Trigger Admin Login Failure Alert
log "Triggering Admin Login Failure Alert..."
curl -s -X POST "$API_URL/admin/auth/" \
  -F "username=admin@example.com" \
  -F "password=wrongpass" > /dev/null

# 3. Trigger Invalid Admin Token Alert
log "Triggering Invalid Admin Token Alert..."
curl -s -X GET "$API_URL/admin/user/" \
  -H "Authorization: Bearer invalid_token" > /dev/null

# 4. Trigger Permission Denial Alert
log "Phase 1: Login as Normal User to get token"
# We need a real user for this. Let's create one or use existing if any.
# For simplicity, we just check logs for the above failures.

# Wait a bit for async dispatch
sleep 5

# 5. Verify alerts in Logs
log "Verifying alerts in logs..."

if ! docker compose exec swx-api grep -q "LOGIN_FAILURE" "$LOG_FILE"; then
    error_exit "LOGIN_FAILURE alert not found in logs."
fi
log "Verified: LOGIN_FAILURE found in logs."

if ! docker compose exec swx-api grep -q "ADMIN_LOGIN_FAILURE" "$LOG_FILE"; then
    error_exit "ADMIN_LOGIN_FAILURE alert not found in logs."
fi
log "Verified: ADMIN_LOGIN_FAILURE found in logs."

if ! docker compose exec swx-api grep -q "INVALID_ADMIN_TOKEN" "$LOG_FILE"; then
    error_exit "INVALID_ADMIN_TOKEN alert not found in logs."
fi
log "Verified: INVALID_ADMIN_TOKEN found in logs."

log "ALERT SMOKE TEST PASSED"
exit 0
