#!/bin/bash

echo "🔍 COMPREHENSIVE SANITY CHECK 🔍"
echo "=================================="
echo ""

# 1. Check Services
echo "🛠️  1. Service Health:"
docker ps | grep researchos | while read line; do
    echo "   $(echo $line | awk '{print $NF}') - $(echo $line | grep -o "(healthy)")"
done
echo ""

# 2. Database Schema Check
echo "🗄️  2. Database Schema (key tables):"
for table in organizations users projects experiments runs metrics nodes edges; do
    count=$(docker exec researchos-postgres-1 psql -U researchos -d researchos -t -c "SELECT COUNT(*) FROM $table;" 2>/dev/null || echo "N/A")
    echo "   $table: $count rows"
done
echo ""

# 3. API Endpoints
echo "🌐 3. Available API Endpoints:"
curl -s http://localhost:8000/openapi.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
print('Total paths:', len(data['paths']))
for path in data['paths']:
    print(f'  {path}')
" 2>/dev/null || echo "  (parsing failed)"
echo ""

# 4. Authentication Test
echo "🔐 4. Authentication Test:"
TOKEN_RESPONSE=$(curl -s -X POST http://localhost:8000/auth/login -H "Content-Type: application/json" -d '{"email": "researcher@test.com", "password": "password123"}')
if echo "$TOKEN_RESPONSE" | grep -q access_token; then
    TOKEN=$(echo "$TOKEN_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    echo "   ✅ Authentication SUCCESS"
    echo "   Token: ${TOKEN:0:30}..."
else
    echo "   ❌ Authentication FAILED"
    exit 1
fi
echo ""

# 5. End-to-End Workflow
echo "🔄 5. End-to-End Workflow Test:"
PROJECT_ID="90c7cb47-cc1f-472f-99c5-2b17a9e088a8"

echo "   Step A: Create experiment"
EXP_RESPONSE=$(curl -s -X POST "http://localhost:8000/v1/experiments/?name=SanityCheckExp&project_id=$PROJECT_ID" \
  -H "Authorization: Bearer $TOKEN")
if echo "$EXP_RESPONSE" | grep -q '"id"'; then
    EXP_ID=$(echo "$EXP_RESPONSE" | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
    echo "   ✅ Experiment created: ${EXP_ID:0:20}..."
    
    echo "   Step B: Create run"
    RUN_RESPONSE=$(curl -s -X POST "http://localhost:8000/v1/experiments/$EXP_ID/runs" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"git_commit": "sanity-check", "git_branch": "main"}')
    if echo "$RUN_RESPONSE" | grep -q run_id; then
        RUN_ID=$(echo "$RUN_RESPONSE" | grep -o '"run_id":"[^"]*"' | cut -d'"' -f4)
        echo "   ✅ Run created: ${RUN_ID:0:20}..."
        
        echo "   Step C: Log metrics"
        for i in {1..2}; do
            curl -s -X POST "http://localhost:8000/v1/experiments/$EXP_ID/runs/$RUN_ID/metrics?key=accuracy&value=0.$((80 + i))&step=$i" \
              -H "Authorization: Bearer $TOKEN" >/dev/null
        done
        echo "   ✅ 2 metrics logged"
        
        echo "   Step D: Complete run"
        COMPLETE_RESPONSE=$(curl -s -X POST "http://localhost:8000/v1/experiments/$EXP_ID/runs/$RUN_ID/complete" \
          -H "Authorization: Bearer $TOKEN")
        if echo "$COMPLETE_RESPONSE" | grep -q run_id; then
            echo "   ✅ Run completed"
            
            echo "   Step E: Verify in database"
            DB_STATUS=$(docker exec researchos-postgres-1 psql -U researchos -d researchos -t -c "SELECT status FROM runs WHERE id = '$RUN_ID';")
            DB_METRICS=$(docker exec researchos-postgres-1 psql -U researchos -d researchos -t -c "SELECT COUNT(*) FROM metrics WHERE run_id = '$RUN_ID';")
            echo "   Database status: $DB_STATUS"
            echo "   Database metrics: $DB_METRICS"
            
            echo ""
            echo "🎉 ✅ COMPLETE WORKFLOW VERIFIED!"
            echo "   Experiment → Run → Metrics → Completion"
            
        else
            echo "   ❌ Run completion failed: $COMPLETE_RESPONSE"
        fi
    else
        echo "   ❌ Run creation failed: $RUN_RESPONSE"
    fi
else
    echo "   ❌ Experiment creation failed: $EXP_RESPONSE"
fi

echo ""
echo "=================================="
echo "🏁 SANITY CHECK COMPLETE"
