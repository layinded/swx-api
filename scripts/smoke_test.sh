#!/bin/bash
#
# Smoke Test Suite for SwX-API Stack
# -----------------------------------
# This script validates that all containers are working correctly.
# One failure fails the entire suite.
#
# Usage:
#   ./scripts/smoke_test.sh
#   ./scripts/smoke_test.sh --verbose
#

set -euo pipefail

# Load .env so DB_USER/DB_NAME match compose (for pg_isready)
if [ -f .env ]; then set -a; . ./.env; set +a; fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VERBOSE=${1:-""}
COMPOSE_FILE=${COMPOSE_FILE:-"docker-compose.yml"}
TIMEOUT=${TIMEOUT:-10}

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✅${NC} $1"
    ((TESTS_PASSED++)) || true
    ((TESTS_TOTAL++)) || true
}

log_error() {
    echo -e "${RED}❌${NC} $1"
    ((TESTS_FAILED++)) || true
    ((TESTS_TOTAL++)) || true
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check if docker compose is available
check_docker_compose() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    elif docker-compose version &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    else
        log_error "docker compose or docker-compose is not available"
        exit 1
    fi
    
    log_success "Docker Compose available: $COMPOSE_CMD"
}

# Wait for service to be healthy
wait_for_service() {
    local service=$1
    local max_attempts=${2:-30}
    local attempt=0
    
    log_info "Waiting for $service to be healthy..."
    
    while [ $attempt -lt $max_attempts ]; do
        if $COMPOSE_CMD -f "$COMPOSE_FILE" ps "$service" | grep -q "healthy\|Up"; then
            log_success "$service is up"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 2
    done
    
    log_error "$service did not become healthy within $((max_attempts * 2)) seconds"
    return 1
}

# Test database connectivity
test_database() {
    log_info "Testing database (db)..."
    
    if ! $COMPOSE_CMD -f "$COMPOSE_FILE" ps db | grep -q "Up"; then
        log_error "Database container is not running"
        return 1
    fi
    
    # Test PostgreSQL connectivity
    if $COMPOSE_CMD -f "$COMPOSE_FILE" exec -T db pg_isready -U "${DB_USER:-postgres}" -d "${DB_NAME:-postgres}" &> /dev/null; then
        log_success "Database accepts connections"
        return 0
    else
        log_error "Database does not accept connections"
        return 1
    fi
}

# Test API health endpoint
test_api_health() {
    log_info "Testing API health endpoint (swx-api)..."
    
    if ! $COMPOSE_CMD -f "$COMPOSE_FILE" ps swx-api | grep -q "Up"; then
        log_error "API container is not running"
        return 1
    fi
    
    # Try health check endpoint internally (no port mapping needed)
    local health_url="http://localhost:8000/api/utils/health-check"
    local response
    
    # First try internal (docker exec), fallback to external
    if response=$($COMPOSE_CMD -f "$COMPOSE_FILE" exec -T swx-api curl -sf -m "$TIMEOUT" "$health_url" 2>/dev/null); then
        if echo "$response" | grep -q "healthy"; then
            log_success "API health check passed (internal)"
            return 0
        else
            log_error "API health check returned unexpected response: $response"
            return 1
        fi
    elif response=$(curl -sf -m "$TIMEOUT" "$health_url" 2>/dev/null); then
        if echo "$response" | grep -q "healthy"; then
            log_success "API health check passed (external)"
            return 0
        else
            log_error "API health check returned unexpected response: $response"
            return 1
        fi
    else
        log_error "API health check endpoint not reachable at $health_url"
        return 1
    fi
}

# Test API root endpoint
test_api_root() {
    log_info "Testing API root endpoint..."
    
    local root_url="http://localhost:8000/"
    local response
    
    # First try internal (docker exec), fallback to external
    if response=$($COMPOSE_CMD -f "$COMPOSE_FILE" exec -T swx-api curl -sf -m "$TIMEOUT" "$root_url" 2>/dev/null); then
        if echo "$response" | grep -q "message"; then
            log_success "API root endpoint responds (internal)"
            return 0
        else
            log_error "API root endpoint returned unexpected response: $response"
            return 1
        fi
    elif response=$(curl -sf -m "$TIMEOUT" "$root_url" 2>/dev/null); then
        if echo "$response" | grep -q "message"; then
            log_success "API root endpoint responds (external)"
            return 0
        else
            log_error "API root endpoint returned unexpected response: $response"
            return 1
        fi
    else
        log_error "API root endpoint not reachable at $root_url"
        return 1
    fi
}

# Test vectorizer-worker (if present)
test_vectorizer_worker() {
    log_info "Testing vectorizer-worker..."
    
    if ! $COMPOSE_CMD -f "$COMPOSE_FILE" ps vectorizer-worker &> /dev/null; then
        log_warning "vectorizer-worker not defined in compose file (skipping)"
        return 0
    fi
    
    if $COMPOSE_CMD -f "$COMPOSE_FILE" ps vectorizer-worker | grep -q "Up"; then
        log_success "vectorizer-worker is running"
        return 0
    else
        log_error "vectorizer-worker is not running"
        return 1
    fi
}

# Test adminer (if present and in dev mode)
test_adminer() {
    log_info "Testing adminer..."
    
    if ! $COMPOSE_CMD -f "$COMPOSE_FILE" ps adminer &> /dev/null; then
        log_warning "adminer not defined in compose file (skipping)"
        return 0
    fi
    
    if $COMPOSE_CMD -f "$COMPOSE_FILE" ps adminer | grep -q "Up"; then
        log_success "adminer is running"
        return 0
    else
        log_error "adminer is not running"
        return 1
    fi
}

# Test reverse proxy (Caddy or Traefik)
test_reverse_proxy() {
    log_info "Testing reverse proxy..."
    
    # Check for Caddy
    if $COMPOSE_CMD -f "$COMPOSE_FILE" ps caddy &> /dev/null; then
        if $COMPOSE_CMD -f "$COMPOSE_FILE" ps caddy | grep -q "Up"; then
            log_success "Caddy is running"
            return 0
        else
            log_error "Caddy is not running"
            return 1
        fi
    fi
    
    # Check for Traefik (legacy - should not exist)
    if $COMPOSE_CMD -f "$COMPOSE_FILE" ps traefik &> /dev/null || $COMPOSE_CMD -f "$COMPOSE_FILE" ps proxy &> /dev/null; then
        log_warning "Traefik/proxy detected (should be removed - use Caddy instead)"
        if $COMPOSE_CMD -f "$COMPOSE_FILE" ps traefik 2>/dev/null | grep -q "Up" || \
           $COMPOSE_CMD -f "$COMPOSE_FILE" ps proxy 2>/dev/null | grep -q "Up"; then
            log_warning "Traefik/proxy is running (migration needed)"
            return 0
        else
            log_warning "Traefik/proxy is not running"
            return 0
        fi
    fi
    
    log_warning "No reverse proxy detected (may be intentional for local dev)"
    return 0
}

# Main test execution
main() {
    echo "=========================================="
    echo "  SwX-API Stack Smoke Test Suite"
    echo "=========================================="
    echo ""
    
    check_docker_compose
    
    echo ""
    echo "Running smoke tests..."
    echo ""
    
    # Core services (must pass)
    test_database || exit 1
    wait_for_service "swx-api" 30 || exit 1
    test_api_health || exit 1
    test_api_root || exit 1
    
    # Optional services (warnings only)
    test_vectorizer_worker || log_warning "vectorizer-worker test failed (non-critical)"
    test_adminer || log_warning "adminer test failed (non-critical)"
    test_reverse_proxy || log_warning "reverse proxy test failed (non-critical)"
    
    echo ""
    echo "=========================================="
    echo "  Test Summary"
    echo "=========================================="
    echo "Total Tests: $TESTS_TOTAL"
    echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
    echo -e "${RED}Failed: $TESTS_FAILED${NC}"
    echo ""
    
    if [ $TESTS_FAILED -eq 0 ]; then
        log_success "All critical tests passed!"
        exit 0
    else
        log_error "Some tests failed. Check output above."
        exit 1
    fi
}

# Run main function
main "$@"
