#!/usr/bin/env bash
#
# Hard Reset for Release Gate / Full System Validation
# ----------------------------------------------------
# Non-interactive. Use for clean-state validation only.
#
# 1. Stop all project containers
# 2. Remove project volumes
# 3. Remove orphan networks
# 4. Remove dangling images
# 5. Clear Python caches
#
# Usage: ./scripts/hard_reset.sh [COMPOSE_FILES]
#   Default: docker-compose.yml only (no override)
#

set -euo pipefail

COMPOSE_FILES="${1:-docker-compose.yml}"
COMPOSE_CMD="docker compose"
if ! docker compose version &>/dev/null; then
  COMPOSE_CMD="docker-compose"
fi

echo "=== Phase 0: Hard Reset ==="
echo "Compose: $COMPOSE_FILES"
echo ""

# 1. Stop all containers and remove volumes
echo "[1/5] Stopping containers and removing volumes..."
$COMPOSE_CMD -f $COMPOSE_FILES down -v --remove-orphans || true

# 2. Remove orphan networks (not used by any container)
echo "[2/5] Pruning orphan networks..."
docker network prune -f

# 3. Remove dangling images
echo "[3/5] Pruning dangling images..."
docker image prune -f

# 4. Optional: remove unused volumes (orphan volumes)
echo "[4/5] Pruning unused volumes..."
docker volume prune -f

# 5. Clear Python caches (project root)
echo "[5/5] Clearing Python caches..."
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
find "$ROOT" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find "$ROOT" -name "*.pyc" -delete 2>/dev/null || true
find "$ROOT" -name "*.pyo" -delete 2>/dev/null || true
# Preserve .venv at project root if present
if [ -d "$ROOT/.venv" ]; then
  find "$ROOT/.venv" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
fi

echo ""
echo "=== Hard reset complete ==="
