#!/bin/bash

echo "🎯 Testing ResearchOS Event System API"
echo "=========================================="

# Get auth token
echo "🔐 Authenticating..."
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "researcher@test.com", "password": "password123"}' | \
  grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "❌ Failed to authenticate"
  exit 1
fi

echo "✅ Authenticated. Token: ${TOKEN:0:20}..."

# Test event endpoints
echo ""
echo "🚀 Testing Event System..."
echo ""

# Test event health endpoint
echo "1. Testing /v1/events/health..."
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/v1/events/health | jq -c '.'

# Test event types
echo ""
echo "2. Testing /v1/events/types..."
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/v1/events/types | jq -c '.[:2]'

# Test stats  
echo ""
echo "3. Testing /v1/events/stats..."
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/v1/events/stats | jq -c '.'

# Test test event emission
echo ""
echo "4. Testing /v1/events/test/emit..."
curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/v1/events/test/emit?event_type=experiment.started" | jq -c '.'

echo ""
echo "=========================================="
echo "✅ Event System API Tests Complete!"

# Check Redis for the emitted event
echo ""
echo "🔍 Checking Redis for events..."
docker exec researchos-redis-1 redis-cli XRANGE events:org_0330725f-579a-4b7f-a013-f34d3577b845 - + | head -20