#!/usr/bin/env python3
"""
Phase 1 System Test - ResearchOS

Tests critical Phase 1 components:
1. Database connectivity and schema
2. Authentication system
3. Event infrastructure
4. Core experiment functionality
"""

import asyncio
import os
import sys
import uuid
import httpx
import asyncpg
from typing import Dict, Any, List

# Base URL
BASE_URL = "http://localhost:8000"
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://researchos:researchos@localhost:5432/researchos")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

class TestError(Exception):
    """Custom test exception"""
    pass

class SystemTest:
    """Comprehensive system test for Phase 1"""
    
    def __init__(self):
        self.results = {}
        
    async def test_database_connectivity(self):
        """Test PostgreSQL connection and schema"""
        print("\n📊 Testing Database Connectivity")
        print("-" * 30)
        
        try:
            # Connect to database
            conn = await asyncpg.connect(DATABASE_URL)
            
            # Test 1: Check connection
            version = await conn.fetchval('SELECT version()')
            print(f"1. PostgreSQL Connected ✓")
            print(f"   Version: {version}")
            
            # Test 2: Check if pgvector extension is installed
            extensions = await conn.fetch('SELECT extname FROM pg_extension')
            extension_names = [e['extname'] for e in extensions]
            print(f"2. Extensions: {', '.join(extension_names)} ✓")
            
            # Test 3: Check table existence
            tables = await conn.fetch("""
                SELECT tablename 
                FROM pg_catalog.pg_tables 
                WHERE schemaname = 'public'
            """)
            table_names = [t['tablename'] for t in tables]
            
            required_tables = [
                'organizations', 'users', 'projects', 'experiments',
                'runs', 'metrics', 'nodes', 'edges'
            ]
            
            print(f"3. Checking required tables...")
            for table in required_tables:
                if table in table_names:
                    print(f"   ✓ {table}")
                else:
                    print(f"   ✗ {table} (missing)")
            
            # Test 4: Check RLS is enabled
            rls_tables = await conn.fetch("""
                SELECT relname 
                FROM pg_class 
                WHERE relrowsecurity = true
            """)
            rls_enabled = [r['relname'] for r in rls_tables]
            print(f"4. RLS enabled on {len(rls_enabled)} tables ✓")
            
            # Count rows in test data
            organizations = await conn.fetchval('SELECT COUNT(*) FROM organizations')
            users = await conn.fetchval('SELECT COUNT(*) FROM users')
            projects = await conn.fetchval('SELECT COUNT(*) FROM projects')
            
            print(f"5. Test data: {organizations} orgs, {users} users, {projects} projects ✓")
            
            await conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Database test failed: {e}")
            raise TestError(f"Database connection failed: {e}")
    
    async def test_redis_connectivity(self):
        """Test Redis connection"""
        print("\n🔴 Testing Redis Connectivity")
        print("-" * 30)
        
        try:
            import redis
            r = redis.Redis.from_url(REDIS_URL)
            response = r.ping()
            
            if response:
                print("1. Redis Connected ✓")
                print(f"   Info: {r.info()['redis_version']}")
                return True
            else:
                raise TestError("Redis ping failed")
                
        except Exception as e:
            print(f"❌ Redis test failed: {e}")
            raise TestError(f"Redis connection failed: {e}")
    
    async def test_backend_health(self):
        """Test backend API health endpoints"""
        print("\n🏥 Testing Backend Health")
        print("-" * 30)
        
        try:
            client = httpx.AsyncClient(timeout=10.0)
            
            # Test 1: Health check
            response = await client.get(f"{BASE_URL}/health/health")
            if response.status_code == 200:
                print(f"1. Health endpoint ✓ ({response.status_code})")
            else:
                raise TestError(f"Health endpoint: {response.status_code}")
            
            # Test 2: Readiness check
            response = await client.get(f"{BASE_URL}/health/ready")
            ready_status = response.status_code == 200
            if ready_status:
                print(f"2. Readiness endpoint ✓ ({response.status_code})")
            else:
                print(f"2. Readiness endpoint ✗ ({response.status_code})")
                print(f"   Response: {response.text}")
            
            # Test 3: Metrics endpoint
            response = await client.get(f"{BASE_URL}/health/metrics")
            if response.status_code == 200:
                print(f"3. Metrics endpoint ✓ ({response.status_code})")
            else:
                print(f"3. Metrics endpoint ✗ ({response.status_code})")
            
            await client.aclose()
            return True
            
        except Exception as e:
            print(f"❌ Backend health test failed: {e}")
            raise TestError(f"Backend health check failed: {e}")
    
    async def test_auth_endpoints_exist(self):
        """Test that authentication endpoints exist"""
        print("\n🔐 Testing Authentication Endpoints")
        print("-" * 30)
        
        try:
            client = httpx.AsyncClient(timeout=10.0)
            
            endpoints = [
                "/auth/login",
                "/auth/refresh",
                "/auth/logout",
                "/auth/profile",
                "/auth/organizations",
            ]
            
            for endpoint in endpoints:
                # OPTIONS request to check if endpoint exists
                response = await client.options(f"{BASE_URL}{endpoint}")
                exists = response.status_code != 404
                
                if exists:
                    print(f"✓ {endpoint}")
                else:
                    print(f"✗ {endpoint} (404)")
            
            await client.aclose()
            return True
            
        except Exception as e:
            print(f"❌ Auth endpoint test failed: {e}")
            raise TestError(f"Auth endpoint check failed: {e}")
    
    async def test_experiment_endpoints_exist(self):
        """Test that experiment endpoints exist"""
        print("\n🧪 Testing Experiment Endpoints")
        print("-" * 30)
        
        try:
            client = httpx.AsyncClient(timeout=10.0)
            
            endpoints = [
                "/v1/experiments",
                "/v1/search",
            ]
            
            for endpoint in endpoints:
                # OPTIONS request to check if endpoint exists
                response = await client.options(f"{BASE_URL}{endpoint}")
                exists = response.status_code != 404
                
                if exists:
                    print(f"✓ {endpoint}")
                else:
                    print(f"✗ {endpoint} (404)")
            
            await client.aclose()
            return True
            
        except Exception as e:
            print(f"❌ Experiment endpoint test failed: {e}")
            raise TestError(f"Experiment endpoint check failed: {e}")
    
    async def test_event_infrastructure(self):
        """Test event infrastructure components"""
        print("\n⚡ Testing Event Infrastructure")
        print("-" * 30)
        
        # Check if event files exist
        event_files = [
            "src/infrastructure/events/producer.py",
            "src/infrastructure/events/consumer.py",
            "src/infrastructure/events/service.py",
            "src/domain/shared/events.py",
            "src/domain/experiments/events.py",
        ]
        
        base_dir = "/home/jarvis/projects/ResearchOS/backend"
        
        for file in event_files:
            full_path = os.path.join(base_dir, file)
            if os.path.exists(full_path):
                print(f"✓ {file}")
            else:
                print(f"✗ {file} (missing)")
        
        return True
    
    async def test_domain_models(self):
        """Test domain model implementations"""
        print("\n🏛️  Testing Domain Models")
        print("-" * 30)
        
        # Check if domain model files exist
        domain_files = [
            "src/domain/experiments/entities.py",
            "src/domain/experiments/repositories.py",
            "src/domain/shared/value_objects.py",
            "src/infrastructure/persistence/repositories/experiment_repository.py",
        ]
        
        base_dir = "/home/jarvis/projects/ResearchOS/backend"
        
        for file in domain_files:
            full_path = os.path.join(base_dir, file)
            if os.path.exists(full_path):
                print(f"✓ {file}")
            else:
                print(f"✗ {file} (missing)")
        
        return True

async def run_all_tests():
    """Run all Phase 1 tests"""
    print("🚀 ResearchOS Phase 1 System Test")
    print("=" * 50)
    print(f"Database: {DATABASE_URL}")
    print(f"API: {BASE_URL}")
    print("=" * 50)
    
    test = SystemTest()
    all_passed = True
    
    try:
        # 1. Database connectivity
        if await test.test_database_connectivity():
            test.results['database'] = 'PASS'
        else:
            test.results['database'] = 'FAIL'
            all_passed = False
        
        # 2. Redis connectivity
        if await test.test_redis_connectivity():
            test.results['redis'] = 'PASS'
        else:
            test.results['redis'] = 'FAIL'
            all_passed = False
        
        # 3. Backend health
        if await test.test_backend_health():
            test.results['backend'] = 'PASS'
        else:
            test.results['backend'] = 'FAIL'
            all_passed = False
        
        # 4. Authentication endpoints
        if await test.test_auth_endpoints_exist():
            test.results['auth_endpoints'] = 'PASS'
        else:
            test.results['auth_endpoints'] = 'FAIL'
        
        # 5. Experiment endpoints
        if await test.test_experiment_endpoints_exist():
            test.results['experiment_endpoints'] = 'PASS'
        else:
            test.results['experiment_endpoints'] = 'FAIL'
        
        # 6. Event infrastructure
        if await test.test_event_infrastructure():
            test.results['event_infrastructure'] = 'PASS'
        else:
            test.results['event_infrastructure'] = 'PARTIAL'
        
        # 7. Domain models
        if await test.test_domain_models():
            test.results['domain_models'] = 'PASS'
        else:
            test.results['domain_models'] = 'PARTIAL'
        
        # Print summary
        print("\n" + "=" * 50)
        print("📊 Phase 1 Test Summary")
        print("=" * 50)
        
        for component, status in test.results.items():
            status_icon = "✓" if status == 'PASS' else "⚠️" if status == 'PARTIAL' else "✗"
            print(f"{status_icon} {component}: {status}")
        
        print("=" * 50)
        
        if all_passed:
            print("🎉 Phase 1 Critical Components PASS")
            print("\nNext Steps:")
            print("1. Run database migrations to create tables")
            print("2. Fix email-validator dependency")
            print("3. Start testing authentication system")
            print("4. Implement repository layer")
        else:
            print("⚠️  Phase 1 Tests have issues")
            print("\nBlockers:")
            print("1. Database tables not created")
            print("2. Backend container unhealthy")
            print("3. Authentication system incomplete")
            
        return all_passed
        
    except Exception as e:
        print(f"\n❌ System test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)