#!/bin/bash
# Quickstart script for ResearchOS Authentication System

set -e

echo "🚀 ResearchOS Authentication System Quickstart"
echo "=============================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# 1. Check if Docker Compose is running
echo "1. Checking services..."
if docker-compose ps | grep -q "Up"; then
    print_status "Services are running"
else
    print_warning "Starting services..."
    docker-compose up -d
    sleep 10
fi

# 2. Run migrations
echo "2. Running migrations..."
if docker-compose exec -T backend alembic upgrade head; then
    print_status "Migrations completed"
else
    print_error "Migrations failed"
    exit 1
fi

# 3. Test login
echo "3. Testing authentication..."
ACCESS_TOKEN=$(curl -s -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test1234","organization_id":"00000000-0000-0000-0000-000000000001"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'][:20] + '...')" 2>/dev/null || echo "")

if [ -n "$ACCESS_TOKEN" ]; then
    print_status "Login successful (Access token: ${ACCESS_TOKEN})"
    
    # 4. Test protected endpoint
    echo "4. Testing protected endpoint..."
    RESPONSE_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
      -X GET "http://localhost:8000/auth/profile" \
      -H "Authorization: Bearer ${ACCESS_TOKEN}")
    
    if [ "$RESPONSE_CODE" = "200" ]; then
        print_status "API endpoint accessible"
        
        # 5. Get user profile
        PROFILE=$(curl -s -X GET "http://localhost:8000/auth/profile" \
          -H "Authorization: Bearer ${ACCESS_TOKEN}")
        
        USER_EMAIL=$(echo "$PROFILE" | python3 -c "import sys, json; print(json.load(sys.stdin)['email'])" 2>/dev/null || echo "Unknown")
        print_status "User: $USER_EMAIL"
        
    else
        print_error "API endpoint failed with code: $RESPONSE_CODE"
    fi
else
    print_error "Login failed"
fi

# 6. Show available endpoints
echo "5. Available endpoints:"
echo "   - POST /auth/login          - Login with email/password"
echo "   - POST /auth/refresh        - Refresh access token"
echo "   - POST /auth/logout         - Logout"
echo "   - POST /auth/api-keys       - Create API key"
echo "   - GET  /auth/profile        - Get user profile"
echo "   - GET  /auth/organizations  - List user's organizations"
echo "   - POST /v1/experiments       - Create experiment"
echo "   - GET  /v1/experiments/{id}  - Get experiment"
echo "   - GET  /health               - Health check (public)"

# 7. Show example commands
echo "6. Example usage:"
echo "   Login:"
echo "     curl -X POST http://localhost:8000/auth/login \\"
echo "       -H \"Content-Type: application/json\" \\"
echo "       -d '{\"email\":\"test@example.com\",\"password\":\"test1234\",\"organization_id\":\"00000000-0000-0000-0000-000000000001\"}'"
echo ""
echo "   Create experiment (after getting token):"
echo "     curl -X POST http://localhost:8000/v1/experiments \\"
echo "       -H \"Authorization: Bearer YOUR_ACCESS_TOKEN\" \\"
echo "       -H \"Content-Type: application/json\" \\"
echo "       -d '{\"name\":\"My Experiment\",\"project_id\":\"00000000-0000-0000-0000-000000000001\",\"description\":\"Test experiment\"}'"
echo ""
echo "   Create API key:"
echo "     curl -X POST http://localhost:8000/auth/api-keys \\"
echo "       -H \"Authorization: Bearer YOUR_ACCESS_TOKEN\" \\"
echo "       -H \"Content-Type: application/json\" \\"
echo "       -d '{\"name\":\"My API Key\",\"expires_at\":null}'"
echo ""
echo "   Use API key:"
echo "     curl -X GET http://localhost:8000/auth/profile \\"
echo "       -H \"X-API-Key: YOUR_API_KEY\""

# 8. Show status
echo "7. System status:"
echo "   - Backend:    http://localhost:8000"
echo "   - PostgreSQL: localhost:5432"
echo "   - Redis:      localhost:6379"
echo "   - MinIO:      localhost:9001"
echo ""
echo "8. Test credentials:"
echo "   - Email:    test@example.com"
echo "   - Password: test1234"
echo "   - Organization ID: 00000000-0000-0000-0000-000000000001"
echo ""
echo "9. Next steps:"
echo "   a. Create more users via API"
echo "   b. Test organization switching"
echo "   c. Test role-based permissions"
echo "   d. Deploy to production with proper secrets"
echo ""
print_status "Authentication system is ready!"
echo ""
print_warning "IMPORTANT: Change default passwords and API keys in production!"
echo "=============================================="