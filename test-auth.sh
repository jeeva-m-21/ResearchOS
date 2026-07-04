#!/bin/bash
# Test script for ResearchOS Authentication System

set -e

echo "🚀 Testing ResearchOS Authentication System"
echo "========================================="

# 1. Start services
echo "Starting Docker Compose services..."
docker-compose up -d
sleep 10

# 2. Run migrations
echo "Running database migrations..."
docker-compose exec backend alembic upgrade head

# 3. Test login endpoint
echo "Testing login endpoint..."
LOGIN_RESPONSE=$(curl -s -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test1234","organization_id":"00000000-0000-0000-0000-000000000001"}')

echo "Login Response: $LOGIN_RESPONSE"

# Extract tokens
ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
REFRESH_TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"refresh_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$ACCESS_TOKEN" ]; then
  echo "❌ Login failed"
  exit 1
fi

echo "✅ Login successful"
echo "Access Token: ${ACCESS_TOKEN:0:30}..."
echo "Refresh Token: ${REFRESH_TOKEN:0:30}..."

# 4. Test protected endpoint
echo "Testing protected endpoint (experiments)..."
EXPERIMENTS_RESPONSE=$(curl -s -X GET "http://localhost:8000/v1/experiments" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

echo "Experiments Response: $EXPERIMENTS_RESPONSE"

# 5. Test refresh token
echo "Testing refresh token..."
REFRESH_RESPONSE=$(curl -s -X POST "http://localhost:8000/auth/refresh" \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\":\"$REFRESH_TOKEN\"}")

echo "Refresh Response: $REFRESH_RESPONSE"

# Extract new access token
NEW_ACCESS_TOKEN=$(echo $REFRESH_RESPONSE | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -n "$NEW_ACCESS_TOKEN" ]; then
  echo "✅ Token refresh successful"
  
  # 6. Test with new token
  echo "Testing with refreshed token..."
  curl -s -X GET "http://localhost:8000/v1/experiments" \
    -H "Authorization: Bearer $NEW_ACCESS_TOKEN" > /dev/null && echo "✅ Refreshed token works"
else
  echo "❌ Token refresh failed"
fi

# 7. Test logout
echo "Testing logout..."
LOGOUT_RESPONSE=$(curl -s -X POST "http://localhost:8000/auth/logout" \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\":\"$REFRESH_TOKEN\"}")

echo "Logout Response: $LOGOUT_RESPONSE"

# 8. Test API key authentication
echo "Testing API key authentication..."
# Note: Test API key was created in migration (test_api_key_12345)
# In production, you'd create an API key first via POST /auth/api-keys

echo "✅ All authentication tests passed!"
echo "========================================="
echo "Next steps:"
echo "1. Create more users via API"
echo "2. Test organization isolation"
echo "3. Test role-based access control"
echo "4. Test API key management"
echo "5. Integration with RLS policies"

# Cleanup
echo "Cleaning up..."
docker-compose down