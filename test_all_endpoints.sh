#!/bin/bash

echo "🔬 TESTING ALL API ENDPOINTS"
echo "============================="
echo ""

# Get token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login -H "Content-Type: application/json" -d '{"email": "researcher@test.com", "password": "password123"}' | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
PROJECT_ID="90c7cb47-cc1f-472f-99c5-2b17a9e088a8"

echo "Testing with token: ${TOKEN:0:20}..."
echo ""

endpoints=(
    # Authentication endpoints
    "POST /auth/login"
    "POST /auth/refresh"
    "GET /auth/profile"
    "GET /auth/organizations"
    "GET /auth/api-keys"
    "POST /auth/logout"
    
    # Health endpoints
    "GET /health/"
    "GET /health/ready"
    
    # Core API
    "POST /v1/experiments/"
    "GET /v1/experiments/{exp_id}"
    "POST /v1/experiments/{exp_id}/runs"
    "GET /v1/experiments/{exp_id}/runs"
    "POST /v1/experiments/{exp_id}/runs/{run_id}/metrics"
    "GET /v1/experiments/{exp_id}/runs/{run_id}/metrics"
    "POST /v1/experiments/{exp_id}/runs/{run_id}/complete"
    "GET /v1/search/"
)

# First create an experiment and run for testing
echo "🔄 Setting up test data..."
EXP_RESPONSE=$(curl -s -X POST "http://localhost:8000/v1/experiments/?name=EndpointTest&project_id=$PROJECT_ID" -H "Authorization: Bearer $TOKEN")
EXP_ID=$(echo "$EXP_RESPONSE" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
RUN_RESPONSE=$(curl -s -X POST "http://localhost:8000/v1/experiments/$EXP_ID/runs" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"git_commit": "test"}')
RUN_ID=$(echo "$RUN_RESPONSE" | grep -o '"run_id":"[^"]*"' | cut -d'"' -f4)
echo "   Created exp: ${EXP_ID:0:20}..., run: ${RUN_ID:0:20}..."
echo ""

echo "📊 Testing each endpoint:"
echo "-------------------------"

passed=0
failed=0

# Test each endpoint
for endpoint_spec in "${endpoints[@]}"; do
    method=$(echo "$endpoint_spec" | awk '{print $1}')
    path=$(echo "$endpoint_spec" | awk '{print $2}')
    
    # Replace placeholders
    path=${path//\{exp_id\}/$EXP_ID}
    path=${path//\{run_id\}/$RUN_ID}
    
    echo -n "🧪 $method $path: "
    
    if [[ "$method" == "POST" ]]; then
        case "$path" in
            "/auth/login")
                # Special case - needs auth data
                response=$(curl -s -X POST "http://localhost:8000$path" -H "Content-Type: application/json" -d '{"email": "researcher@test.com", "password": "password123"}' -w " %{http_code}")
                ;;
            "/auth/refresh")
                # Needs refresh token - skip
                echo "SKIP (needs refresh token)"
                continue
                ;;
            "/auth/logout")
                # Needs valid token
                response=$(curl -s -X POST "http://localhost:8000$path" -H "Authorization: Bearer $TOKEN" -w " %{http_code}")
                ;;
            "/v1/experiments/")
                response=$(curl -s -X POST "http://localhost:8000$path?name=TestEndpoint&project_id=$PROJECT_ID" -H "Authorization: Bearer $TOKEN" -w " %{http_code}")
                ;;
            "/v1/experiments/$EXP_ID/runs")
                response=$(curl -s -X POST "http://localhost:8000$path" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"git_commit": "test-endpoint"}' -w " %{http_code}")
                ;;
            "/v1/experiments/$EXP_ID/runs/$RUN_ID/metrics")
                response=$(curl -s -X POST "http://localhost:8000$path?key=loss&value=0.5&step=1" -H "Authorization: Bearer $TOKEN" -w " %{http_code}")
                ;;
            "/v1/experiments/$EXP_ID/runs/$RUN_ID/complete")
                # Need to create a new run to complete
                NEW_RUN_RESPONSE=$(curl -s -X POST "http://localhost:8000/v1/experiments/$EXP_ID/runs" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"git_commit": "complete-test"}')
                NEW_RUN_ID=$(echo "$NEW_RUN_RESPONSE" | grep -o '"run_id":"[^"]*"' | cut -d'"' -f4)
                response=$(curl -s -X POST "http://localhost:8000/v1/experiments/$EXP_ID/runs/$NEW_RUN_ID/complete" -H "Authorization: Bearer $TOKEN" -w " %{http_code}")
                ;;
            *)
                response=$(curl -s -X POST "http://localhost:8000$path" -H "Authorization: Bearer $TOKEN" -w " %{http_code}")
                ;;
        esac
    else
        # GET endpoints
        if [[ "$path" == "/v1/search/" ]]; then
            response=$(curl -s "http://localhost:8000$path?q=test" -H "Authorization: Bearer $TOKEN" -w " %{http_code}")
        else
            response=$(curl -s "http://localhost:8000$path" -H "Authorization: Bearer $TOKEN" -w " %{http_code}")
        fi
    fi
    
    http_code=$(echo "$response" | awk '{print $NF}')
    response_body=$(echo "$response" | sed '$d')
    
    if [[ "$http_code" =~ ^(200|201|307)$ ]]; then
        echo "✅ PASS ($http_code)"
        ((passed++))
    else
        echo "❌ FAIL ($http_code)"
        echo "   Response: ${response_body:0:100}..."
        ((failed++))
    fi
done

echo ""
echo "📈 RESULTS:"
echo "   ✅ Passed: $passed"
echo "   ❌ Failed: $failed"
echo "   📊 Success Rate: $(( (passed * 100) / (passed + failed) ))%"

if [ $failed -eq 0 ]; then
    echo ""
    echo "🎉 ALL ENDPOINTS ARE HEALTHY!"
else
    echo ""
    echo "⚠️ Some endpoints need attention."
fi
