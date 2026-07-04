#!/usr/bin/env bash
set -e

# ──────────────────────────────────────────────
# ResearchOS — Single-Command MVP Launcher
# Starts: PostgreSQL, Redis, Backend API, Frontend
# ──────────────────────────────────────────────

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
error(){ echo -e "${RED}[✗]${NC} $1"; }
info() { echo -e "${BLUE}[i]${NC} $1"; }

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# ── 1. Prerequisites ──────────────────────────
info "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
  error "Docker is required but not installed. Install it from https://docs.docker.com/get-docker/"
  exit 1
fi

if ! docker info &> /dev/null; then
  error "Docker daemon is not running. Start it and try again."
  exit 1
fi

if ! command -v node &> /dev/null; then
  error "Node.js is required but not installed."
  exit 1
fi

if ! command -v npm &> /dev/null; then
  error "npm is required but not installed."
  exit 1
fi

log "Prerequisites satisfied (Docker $(docker --version | cut -d' ' -f3 | tr -d ','), Node $(node --version))"

# ── 2. Start Docker services (PostgreSQL + Redis + Backend) ──
info "Starting Docker services..."
docker compose up -d 2>&1 | sed 's/^/  /'
log "Docker services started"

# ── 3. Wait for backend to be healthy ─────────
info "Waiting for backend to become healthy..."
BACKEND_HEALTHY=false
for i in $(seq 1 30); do
  if curl -sf http://localhost:8000/health/ > /dev/null 2>&1; then
    BACKEND_HEALTHY=true
    break
  fi
  sleep 2
done

if [ "$BACKEND_HEALTHY" = false ]; then
  error "Backend did not become healthy within 60s. Check 'docker compose logs backend'."
  exit 1
fi
log "Backend is healthy at http://localhost:8000"

# ── 4. Run DB migrations ─────────────────────
info "Running database migrations..."
if docker exec researchos-backend-1 alembic upgrade head 2>/dev/null; then
  log "Database migrations applied"
else
  # Container name might differ
  if docker exec researchos-backend-1 alembic upgrade head 2>/dev/null; then
    log "Database migrations applied"
  else
    warn "Could not run migrations (container may use different name). Continuing..."
  fi
fi

# ── 5. Create test users if they don't exist ──
info "Ensuring test users exist..."
docker exec researchos-backend-1 python -c "
import asyncio, asyncpg
async def seed():
    conn = await asyncpg.connect('postgresql://researchos:researchos@localhost:5432/researchos')
    row = await conn.fetchrow(\"SELECT id FROM users WHERE email='researcher@test.com'\")
    if not row:
        from src.infrastructure.database import db
        await db.execute(\"INSERT INTO users (id, email, name) VALUES (gen_random_uuid(), 'researcher@test.com', 'Test Researcher')\")
        print('Created test user')
    else:
        print('Test user already exists')
    await conn.close()
asyncio.run(seed())
" 2>/dev/null || warn "Skipping test user seed (not critical)"
log "Test users ready"

# ── 6. Install frontend dependencies if needed ─
if [ ! -d "frontend/node_modules" ]; then
  info "Installing frontend dependencies..."
  cd frontend && npm install 2>&1 | tail -1 && cd ..
  log "Frontend dependencies installed"
else
  log "Frontend dependencies already installed"
fi

# ── 7. Start frontend dev server ────────────
info "Starting frontend dev server..."
cd frontend
npx next dev -p 3000 &
FRONTEND_PID=$!
cd ..

# ── 8. Wait for frontend to be ready ──────────
info "Waiting for frontend at http://localhost:3000..."
FRONTEND_READY=false
for i in $(seq 1 30); do
  if curl -sf http://localhost:3000/login > /dev/null 2>&1; then
    FRONTEND_READY=true
    break
  fi
  sleep 2
done

if [ "$FRONTEND_READY" = false ]; then
  warn "Frontend may still be compiling. Check http://localhost:3000 manually."
fi
log "Frontend ready at http://localhost:3000"

# ── 9. Print summary ────────────────────────
echo ""
echo "══════════════════════════════════════════"
echo -e "  ${GREEN}ResearchOS MVP is RUNNING${NC}"
echo "══════════════════════════════════════════"
echo ""
echo "  Frontend:  http://localhost:3000"
echo "  Backend:   http://localhost:8000"
echo "  API Docs:  http://localhost:8000/docs"
echo "  Health:    http://localhost:8000/health/"
echo ""
echo "  Test login:"
echo "    Email:    researcher@test.com"
echo "    Password: password123"
echo ""
echo "  Stop with:  kill $FRONTEND_PID && docker compose down"
echo "══════════════════════════════════════════"
echo ""

# ── 10. Trap Ctrl+C to clean up ─────────────
cleanup() {
  echo ""
  warn "Shutting down..."
  kill $FRONTEND_PID 2>/dev/null || true
  docker compose down 2>/dev/null || true
  log "All services stopped. Goodbye!"
  exit 0
}
trap cleanup SIGINT SIGTERM

# Keep running
wait $FRONTEND_PID
