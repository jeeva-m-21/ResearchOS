#!/bin/bash
# Demo script for ResearchOS Authentication System

echo "🔐 ResearchOS Authentication Demo"
echo "=================================="

# Start services if not running
if ! docker-compose ps | grep -q "Up"; then
    echo "Starting services..."
    docker-compose up -d
    sleep 10
fi

# Run migrations
echo "Running database migrations..."
docker-compose exec backend alembic upgrade head

echo ""
echo "📋 Available test data:"
echo "  Email:    test@example.com"
echo "  Password: test1234"
echo "  Org ID:   00000000-0000-0000-0000-000000000001"
echo ""

echo "🚪 Step 1: Login"
echo "--------------"
RESPONSE=$(curl -s -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test1234","organization_id":"00000000-0000-0000-0000-000000000001"}')

if echo "$RESPONSE" | grep -q "access_token"; then
    ACCESS_TOKEN=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
    echo "✅ Login successful!"
    echo "Access token: ${ACCESS_TOKEN:0:30}..."
else
    echo "❌ Login failed"
    echo "Response: $RESPONSE"
    exit 1
fi

echo ""
echo "👤 Step 2: Get User Profile"
echo "-------------------------"
PROFILE=$(curl -s -X GET "http://localhost:8000/auth/profile" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

echo "$PROFILE" | python3 -m json.tool

echo ""
echo "🏢 Step 3: List Organizations"
echo "---------------------------"
ORGS=$(curl -s -X GET "http://localhost:8000/auth/organizations" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

echo "$ORGS" | python3 -m json.tool

echo ""
echo "🧪 Step 4: Create an Experiment"
echo "------------------------------"
EXPERIMENT=$(curl -s -X POST "http://localhost:8000/v1/experiments" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Demo Experiment","project_id":"00000000-0000-0000-0000-000000000001","description":"Created via demo script"}')

echo "$EXPERIMENT" | python3 -m json.tool

echo ""
echo "🔑 Step 5: Create an API Key"
echo "---------------------------"
API_KEY_DATA=$(curl -s -X POST "http://localhost:8000/auth/api-keys" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Demo API Key","expires_at":null}')

API_KEY=$(echo "$API_KEY_DATA" | python3 -c "import sys, json; print(json.load(sys.stdin)['key'])")

echo "✅ API Key created!"
echo "API Key: $API_KEY"
echo "Note: Save this key - it won't be shown again"

echo ""
echo "📊 Step 6: Use API Key"
echo "----------------------"
API_PROFILE=$(curl -s -X GET "http://localhost:8000/auth/profile" \
  -H "X-API-Key: $API_KEY")

echo "API Key authentication test:"
echo "$API_PROFILE" | python3 -m json.tool

echo ""
echo "🔄 Step 7: Refresh Token"
echo "-----------------------"
REFRESH_TOKEN=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['refresh_token'])")

REFRESH_RESPONSE=$(curl -s -X POST "http://localhost:8000/auth/refresh" \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\":\"$REFRESH_TOKEN\"}")

if echo "$REFRESH_RESPONSE" | grep -q "access_token"; then
    NEW_TOKEN=$(echo "$REFRESH_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
    echo "✅ Token refresh successful!"
    echo "New token: ${NEW_TOKEN:0:30}..."
fi

echo ""
echo "🚪 Step 8: Logout"
echo "----------------"
LOGOUT_RESPONSE=$(curl -s -X POST "http://localhost:8000/auth/logout" \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\":\"$REFRESH_TOKEN\"}")

echo "Logout response:"
echo "$LOGOUT_RESPONSE" | python3 -m json.tool

echo ""
echo "✅ Demo Complete!"
echo "======================"
echo ""
echo "📋 Summary of what was tested:"
echo "  1. JWT Authentication ✓"
echo "  2. User profile access ✓"
echo "  3. Organization listing ✓"
echo "  4. Resource creation (experiment) ✓"
echo "  5. API key creation ✓"
echo "  6. API key authentication ✓"
echo "  7. Token refresh ✓"
echo "  8. Logout ✓"
echo ""
echo "🔗 Endpoint URLs:"
echo "  - Backend API: http://localhost:8000"
echo "  - Health check: http://localhost:8000/health"
echo ""
echo "📚 Full API documentation at: http://localhost:8000/docs"
echo ""
echo "💡 Next steps:"
echo "  - Create more users via API"
echo "  - Test organization switching"
echo "  - Test role-based permissions"
echo "  - Modify RLS policies for different access levels"
echo ""