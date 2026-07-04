#!/usr/bin/env python3
"""
Test Event System Integration

This script tests the newly implemented Event System API endpoints.
Run it after starting the ResearchOS backend server.
"""

import asyncio
import httpx
import json
from uuid import uuid4
from datetime import datetime

API_BASE = "http://localhost:8000"


async def get_auth_token():
    """Get authentication token for testing"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE}/auth/login",
            json={
                "email": "researcher@test.com",
                "password": "password123"
            }
        )
        
        if response.status_code != 200:
            print(f"❌ Authentication failed: {response.text}")
            return None
        
        data = response.json()
        return data.get("access_token")


async def test_event_endpoints():
    """Test event API endpoints"""
    token = await get_auth_token()
    if not token:
        print("Skipping event tests - authentication failed")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient(headers=headers) as client:
        print("🚀 Testing Event System API...")
        
        # 1. Test health endpoint
        print("\n1. Testing /v1/events/health...")
        try:
            response = await client.get(f"{API_BASE}/v1/events/health")
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # 2. Test event types endpoint
        print("\n2. Testing /v1/events/types...")
        try:
            response = await client.get(f"{API_BASE}/v1/events/types")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                types = response.json()
                print(f"   Found {len(types)} event types")
                for t in types[:3]:
                    print(f"   - {t['type']}: {t['description']}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # 3. Test stats endpoint
        print("\n3. Testing /v1/events/stats...")
        try:
            response = await client.get(f"{API_BASE}/v1/events/stats")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                stats = response.json()
                print(f"   Stream info: {json.dumps(stats, indent=2)[:300]}...")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # 4. Test test event emission
        print("\n4. Testing /v1/events/test/emit...")
        try:
            response = await client.post(
                f"{API_BASE}/v1/events/test/emit",
                params={"event_type": "experiment.started"}
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Event emitted: {result.get('event_id')}")
                print(f"   Stream ID: {result.get('stream_id')}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # 5. Test emit real event
        print("\n5. Testing /v1/events/emit...")
        try:
            event_data = {
                "event_id": str(uuid4()),
                "event_type": "experiment.started",
                "aggregate_id": str(uuid4()),
                "aggregate_type": "Experiment",
                "version": 1,
                "timestamp": datetime.utcnow().isoformat(),
                "organization_id": "0330725f-579a-4b7f-a013-f34d3577b845",
                "experiment_id": str(uuid4()),
                "project_id": str(uuid4()),
                "started_by": "00000000-0000-0000-0000-000000000000",
                "created_by": "00000000-0000-0000-0000-000000000000",
                "name": "API Test Experiment",
                "description": "Created via API test",
                "tags": ["test", "api"]
            }
            
            response = await client.post(
                f"{API_BASE}/v1/events/emit",
                json=event_data
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Event emitted successfully")
                print(f"   Event ID: {result.get('event_id')}")
                print(f"   Stream ID: {result.get('stream_id')}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n✅ Event System API Tests Complete!")


async def test_integrated_emission():
    """Test event emission from existing experiment endpoints"""
    token = await get_auth_token()
    if not token:
        print("Skipping integrated tests - authentication failed")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient(headers=headers) as client:
        print("\n🔗 Testing Integrated Event Emission...")
        
        # 1. Create an experiment (should emit event)
        print("\n1. Creating experiment...")
        try:
            response = await client.post(
                f"{API_BASE}/v1/experiments/?name=EventTest&project_id=0675acd0-8362-45ab-a3cf-6c05d34809f4&description=Testing+Event+Emission"
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                experiment = response.json()
                experiment_id = experiment.get('id')
                print(f"   ✅ Experiment created: {experiment_id}")
                
                # 2. Log a metric (should emit event)
                print("\n2. Logging metric...")
                response = await client.post(
                    f"{API_BASE}/v1/experiments/{experiment_id}/runs",
                    json={"git_commit": "test123", "git_branch": "main"}
                )
                if response.status_code == 200:
                    run_data = response.json()
                    run_id = run_data.get('id')
                    print(f"   ✅ Run created: {run_id}")
                    
                    # Log metric
                    response = await client.post(
                        f"{API_BASE}/v1/experiments/{experiment_id}/runs/{run_id}/metrics?key=test_accuracy&value=0.95&step=1"
                    )
                    print(f"   Metric log status: {response.status_code}")
                    if response.status_code == 200:
                        print("   ✅ Metric logged (should have emitted event)")
                    
                    # Complete run
                    response = await client.post(
                        f"{API_BASE}/v1/experiments/{experiment_id}/runs/{run_id}/complete"
                    )
                    print(f"   Run complete status: {response.status_code}")
            else:
                print(f"   ❌ Failed to create experiment: {response.text}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n✅ Integrated Event Emission Tests Complete!")


async def main():
    """Main test runner"""
    print("🎯 ResearchOS Event System Integration Tests")
    print("=" * 50)
    
    # First check if server is running
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE}/health/")
            if response.status_code != 200:
                print("❌ Backend server is not running!")
                print("   Start it with: docker compose up -d backend")
                return
            print("✅ Backend server is running")
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        print("   Make sure the backend is running on localhost:8000")
        return
    
    # Run tests
    await test_event_endpoints()
    await test_integrated_emission()
    
    print("\n" + "=" * 50)
    print("🎉 All tests completed!")
    print("\nNext steps:")
    print("1. Check Redis stream: docker exec researchos-redis-1 redis-cli XRANGE events:org_0330725f-579a-4b7f-a013-f34d3577b845 - +")
    print("2. Check event projections in database")
    print("3. Verify consumer groups are processing events")


if __name__ == "__main__":
    asyncio.run(main())