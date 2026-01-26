#!/bin/bash
#
# Docker Garbage Collection Script
# ---------------------------------
# Safely removes unused Docker resources without affecting running containers.
#
# Usage:
#   ./scripts/docker_cleanup.sh [--dry-run] [--force]
#
# Options:
#   --dry-run    Show what would be removed without actually removing
#   --force      Skip confirmation prompts
#

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Parse arguments
DRY_RUN=false
FORCE=false

for arg in "$@"; do
    case $arg in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        *)
            echo "Unknown option: $arg"
            exit 1
            ;;
    esac
done

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✅${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}❌${NC} $1"
}

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed or not in PATH"
    exit 1
fi

# Get running container IDs
get_running_containers() {
    docker ps -q
}

# Get all container IDs (including stopped)
get_all_containers() {
    docker ps -aq
}

# Get images used by running containers
get_used_images() {
    docker ps --format "{{.Image}}" | sort -u
}

# Confirmation prompt
confirm() {
    if [ "$FORCE" = true ]; then
        return 0
    fi
    
    local message=$1
    read -p "$message (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        return 0
    else
        return 1
    fi
}

# Main cleanup function
main() {
    echo "=========================================="
    echo "  Docker Garbage Collection"
    echo "=========================================="
    echo ""
    
    if [ "$DRY_RUN" = true ]; then
        log_warning "DRY RUN MODE - No changes will be made"
        echo ""
    fi
    
    # Get running containers
    RUNNING_CONTAINERS=$(get_running_containers)
    RUNNING_COUNT=$(echo "$RUNNING_CONTAINERS" | wc -l)
    
    log_info "Running containers: $RUNNING_COUNT"
    if [ "$RUNNING_COUNT" -gt 0 ]; then
        echo "$RUNNING_CONTAINERS" | while read -r container; do
            if [ -n "$container" ]; then
                log_info "  - $(docker ps --format "{{.Names}} ({{.Image}})" --filter "id=$container")"
            fi
        done
    fi
    echo ""
    
    # 1. Remove stopped containers
    log_info "Checking for stopped containers..."
    STOPPED_CONTAINERS=$(docker ps -aq --filter "status=exited")
    STOPPED_COUNT=$(echo "$STOPPED_CONTAINERS" | grep -c . || echo "0")
    
    if [ "$STOPPED_COUNT" -gt 0 ]; then
        log_warning "Found $STOPPED_COUNT stopped container(s)"
        if [ "$DRY_RUN" = true ]; then
            echo "$STOPPED_CONTAINERS" | while read -r container; do
                if [ -n "$container" ]; then
                    log_info "  Would remove: $(docker ps -a --format "{{.Names}} ({{.Image}})" --filter "id=$container")"
                fi
            done
        else
            if confirm "Remove $STOPPED_COUNT stopped container(s)?"; then
                echo "$STOPPED_CONTAINERS" | xargs -r docker rm
                log_success "Removed stopped containers"
            fi
        fi
    else
        log_success "No stopped containers found"
    fi
    echo ""
    
    # 2. Remove dangling images
    log_info "Checking for dangling images..."
    DANGLING_IMAGES=$(docker images -q -f "dangling=true")
    DANGLING_COUNT=$(echo "$DANGLING_IMAGES" | grep -c . || echo "0")
    
    if [ "$DANGLING_COUNT" -gt 0 ]; then
        log_warning "Found $DANGLING_COUNT dangling image(s)"
        if [ "$DRY_RUN" = true ]; then
            echo "$DANGLING_IMAGES" | while read -r image; do
                if [ -n "$image" ]; then
                    log_info "  Would remove: $image"
                fi
            done
        else
            if confirm "Remove $DANGLING_COUNT dangling image(s)?"; then
                echo "$DANGLING_IMAGES" | xargs -r docker rmi
                log_success "Removed dangling images"
            fi
        fi
    else
        log_success "No dangling images found"
    fi
    echo ""
    
    # 3. Remove unused images (not used by any container)
    log_info "Checking for unused images..."
    USED_IMAGES=$(get_used_images)
    ALL_IMAGES=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep -v "<none>")
    
    UNUSED_COUNT=0
    UNUSED_IMAGES=""
    
    while IFS= read -r image; do
        if [ -z "$image" ]; then
            continue
        fi
        
        # Skip if image is used by running container
        if echo "$USED_IMAGES" | grep -q "^${image}$"; then
            continue
        fi
        
        # Skip if image is used by any container (running or stopped)
        if docker ps -a --format "{{.Image}}" | grep -q "^${image}$"; then
            continue
        fi
        
        UNUSED_IMAGES="${UNUSED_IMAGES}${image}\n"
        ((UNUSED_COUNT++)) || true
    done <<< "$ALL_IMAGES"
    
    if [ "$UNUSED_COUNT" -gt 0 ]; then
        log_warning "Found $UNUSED_COUNT unused image(s)"
        if [ "$DRY_RUN" = true ]; then
            echo -e "$UNUSED_IMAGES" | while read -r image; do
                if [ -n "$image" ]; then
                    log_info "  Would remove: $image"
                fi
            done
        else
            if confirm "Remove $UNUSED_COUNT unused image(s)?"; then
                echo -e "$UNUSED_IMAGES" | xargs -r -I {} docker rmi {} 2>/dev/null || true
                log_success "Removed unused images"
            fi
        fi
    else
        log_success "No unused images found"
    fi
    echo ""
    
    # 4. Remove orphan volumes (not used by any container)
    log_info "Checking for orphan volumes..."
    ORPHAN_VOLUMES=$(docker volume ls -q -f "dangling=true")
    ORPHAN_COUNT=$(echo "$ORPHAN_VOLUMES" | grep -c . || echo "0")
    
    if [ "$ORPHAN_COUNT" -gt 0 ]; then
        log_warning "Found $ORPHAN_COUNT orphan volume(s)"
        if [ "$DRY_RUN" = true ]; then
            echo "$ORPHAN_VOLUMES" | while read -r volume; do
                if [ -n "$volume" ]; then
                    log_info "  Would remove: $volume"
                fi
            done
        else
            if confirm "Remove $ORPHAN_COUNT orphan volume(s)? (WARNING: This may delete data)"; then
                echo "$ORPHAN_VOLUMES" | xargs -r docker volume rm
                log_success "Removed orphan volumes"
            fi
        fi
    else
        log_success "No orphan volumes found"
    fi
    echo ""
    
    # 5. Remove unused networks (not used by any container)
    log_info "Checking for unused networks..."
    # Get networks used by containers
    USED_NETWORKS=$(docker ps --format "{{.Networks}}" | tr ',' '\n' | sort -u)
    # Get all networks (excluding default built-ins)
    ALL_NETWORKS=$(docker network ls --format "{{.Name}}" | grep -v "^bridge$\|^host$\|^none$")
    
    UNUSED_NETWORK_COUNT=0
    UNUSED_NETWORKS=""
    
    while IFS= read -r network; do
        if [ -z "$network" ]; then
            continue
        fi
        
        # Skip if network is used
        if echo "$USED_NETWORKS" | grep -q "^${network}$"; then
            continue
        fi
        
        # Skip if network has containers
        if [ "$(docker network inspect "$network" --format '{{len .Containers}}')" -gt 0 ]; then
            continue
        fi
        
        UNUSED_NETWORKS="${UNUSED_NETWORKS}${network}\n"
        ((UNUSED_NETWORK_COUNT++)) || true
    done <<< "$ALL_NETWORKS"
    
    if [ "$UNUSED_NETWORK_COUNT" -gt 0 ]; then
        log_warning "Found $UNUSED_NETWORK_COUNT unused network(s)"
        if [ "$DRY_RUN" = true ]; then
            echo -e "$UNUSED_NETWORKS" | while read -r network; do
                if [ -n "$network" ]; then
                    log_info "  Would remove: $network"
                fi
            done
        else
            if confirm "Remove $UNUSED_NETWORK_COUNT unused network(s)?"; then
                echo -e "$UNUSED_NETWORKS" | xargs -r -I {} docker network rm {} 2>/dev/null || true
                log_success "Removed unused networks"
            fi
        fi
    else
        log_success "No unused networks found"
    fi
    echo ""
    
    # 6. Prune build cache (optional)
    log_info "Checking build cache..."
    CACHE_SIZE=$(docker system df --format "{{.Size}}" | head -1 || echo "0B")
    log_info "Build cache size: $CACHE_SIZE"
    
    if [ "$DRY_RUN" = true ]; then
        log_info "  Would prune build cache (use 'docker builder prune' manually)"
    else
        if confirm "Prune build cache? (This may free significant disk space)"; then
            docker builder prune -f
            log_success "Pruned build cache"
        fi
    fi
    echo ""
    
    # Summary
    echo "=========================================="
    echo "  Cleanup Summary"
    echo "=========================================="
    
    if [ "$DRY_RUN" = true ]; then
        log_warning "DRY RUN - No changes were made"
        echo ""
        log_info "Run without --dry-run to perform cleanup"
    else
        log_success "Cleanup complete!"
        echo ""
        log_info "Disk usage:"
        docker system df
    fi
}

# Run main function
main "$@"
