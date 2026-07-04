#!/bin/bash

echo "=== MANUAL TEST RUNNER ==="
echo ""

TOKEN=$(curl -s -X POST http://localhost:8000/auth/login -H "Content-Type: application/json" -d '{"email": "researcher@test.com", "password": "password123"}' | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
PROJECT_ID="90c7cb47-cc1f-472f-99c5-2b17a9e088a8"

tests_passed=0
tests_failed=0

# Test 1: Health
echo "🧪 Test 1: Health endpoint"
if curl -s http://localhost:8000/health/ | grep -q '"status":"healthy"'; then
    echo "✅ PASS"
    ((tests_passed++))
else
    echo "❌ FAIL"
    ((tests_failed++))
fi

# Test 2: Authentication
echo "🧪 Test 2: Authentication"
if [ -n "$TOKEN" ]; then
    echo "✅ PASS (Token: ${TOKEN:0:20}...)"
    ((tests_passed++))
else
    echo "❌ FAIL"
    ((tests_failed++))
fi

# Test 3: Experiment creation
echo "🧪 Test 3: Experiment creation"
EXP_RESPONSE=$(curl -s -X POST "http://localhost:8000/v1/experiments/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"project_id": "'"$PROJECT_ID"'", "name": "Manual Test Run Experiment", "description": "Testing from manual runner"}')

if echo "$EXP_RESPONSE" | grep -q '"id"'; then
    EXP_ID=$(echo "$EXP_RESPONSE" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
    echo "✅ PASS (Exp: ${EXP_ID:0:20}...)"
    ((tests_passed++))
else
    echo "❌ FAIL: $EXP_RESPONSE"
    ((tests_failed++))
fi

# Test 4: Run creation
echo "🧪 Test 4: Run creation"
RUN_RESPONSE=$(curl -s -X POST "http://localhost:8000/v1/experiments/$EXP_ID/runs" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"git_commit": "manual-test", "git_branch": "main"}')

if echo "$RUN_RESPONSE" | grep -q '"id"'; then
    RUN_ID=$(echo "$RUN_RESPONSE" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
    echo "✅ PASS (Run: ${RUN_ID:0:20}...)"
    ((tests_passed++))
else
    echo "❌ FAIL: $RUN_RESPONSE"
    ((tests_failed++))
fi

# Test 5: Metric logging
echo "🧪 Test 5: Metric logging"
METRIC_RESPONSE=$(curl -s -X POST "http://localhost:8000/v1/experiments/$EXP_ID/runs/$RUN_ID/metrics?key=accuracy&value=0.92&step=1" \
  -H "Authorization: Bearer $TOKEN")

if echo "$METRIC_RESPONSE" | grep -q '"id"'; then
    echo "✅ PASS"
    ((tests_passed++))
else
    echo "❌ FAIL: $METRIC_RESPONSE"
    ((tests_failed++))
fi

# Test 6: Metric retrieval
echo "🧪 Test 6: Metric retrieval"
METRICS=$(curl -s "http://localhost:8000/v1/experiments/$EXP_ID/runs/$RUN_ID/metrics" \
  -H "Authorization: Bearer $TOKEN")

if echo "$METRICS" | grep -q '"key":"accuracy"'; then
    echo "✅ PASS"
    ((tests_passed++))
else
    echo "❌ FAIL: $METRICS"
    ((tests_failed++))
fi

# Test 7: Run completion
echo "🧪 Test 7: Run completion"
COMPLETE_RESPONSE=$(curl -s -X POST "http://localhost:8000/v1/experiments/$EXP_ID/runs/$RUN_ID/complete" \
  -H "Authorization: Bearer $TOKEN")

if echo "$COMPLETE_RESPONSE" | grep -q '"run_id"'; then
    echo "✅ PASS"
    ((tests_passed++))
else
    echo "❌ FAIL: $COMPLETE_RESPONSE"
    ((tests_failed++))
fi

# Test 8: Run status after completion
echo "🧪 Test 8: Run status check"
RUN_STATUS=$(curl -s "http://localhost:8000/v1/experiments/$EXP_ID/runs/$RUN_ID" \
  -H "Authorization: Bearer $TOKEN")

if echo "$RUN_STATUS" | grep -q '"status":"completed"'; then
    echo "✅ PASS"
    ((tests_passed++))
else
    echo "❌ FAIL: $RUN_STATUS"
    ((tests_failed++))
fi

echo ""
echo "=== TEST SUMMARY ==="
echo "✅ Tests Passed: $tests_passed"
echo "❌ Tests Failed: $tests_failed"
echo "📊 Success Rate: $(( (tests_passed * 100) / (tests_passed + tests_failed) ))%"

if [ $tests_failed -eq 0 ]; then
    echo ""
    echo "🎉 ALL TESTS PASSED! ResearchOS is HEALTHY!"
else
    echo ""
    echo "⚠️ Some tests failed. Check logs above."
fi
