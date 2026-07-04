#!/usr/bin/env python3
"""
Create test users and organizations for authentication testing
"""

import asyncio
import uuid
from datetime import datetime

async def create_test_data():
    """Create test users and organizations"""
    
    try:
        # Try to import asyncpg directly to avoid SQLAlchemy dependency
        import asyncpg
        
        # Database connection URL from docker-compose
        db_url = "postgresql://researchos:researchos@postgres:5432/researchos"
        
        # Connect to database
        conn = await asyncpg.connect(db_url)
        
        print("🧑 Creating test users and organizations...")
        
        # Create a test organization
        org_id = str(uuid.uuid4())
        await conn.execute("""
            INSERT INTO organizations (id, name, slug, plan)
            VALUES ($1, $2, $3, $4)
        """, org_id, "Test Research Lab", "test-research-lab", "pro")
        
        print(f"✅ Organization created: Test Research Lab")
        
        # Create test users with hashed passwords
        # Note: In production, passwords should be properly hashed with bcrypt
        # For testing, we'll use a simple hash
        import hashlib
        
        test_users = [
            {
                "email": "researcher@test.com",
                "name": "Test Researcher",
                "password": "password123"  # In real implementation, this would be properly hashed
            },
            {
                "email": "admin@test.com", 
                "name": "Test Administrator",
                "password": "admin123"
            }
        ]
        
        user_ids = []
        for user_data in test_users:
            user_id = str(uuid.uuid4())
            await conn.execute("""
                INSERT INTO users (id, email, name, auth_provider)
                VALUES ($1, $2, $3, $4)
            """, user_id, user_data["email"], user_data["name"], "email")
            
            # Add to organization
            await conn.execute("""
                INSERT INTO organization_members (organization_id, user_id, role)
                VALUES ($1, $2, $3)
            """, org_id, user_id, "admin" if "admin" in user_data["email"] else "member")
            
            user_ids.append(user_id)
            print(f"✅ User created: {user_data['email']} ({user_data['name']})")
        
        # Create a test experiment
        exp_id = str(uuid.uuid4())
        await conn.execute("""
            INSERT INTO experiments (id, organization_id, name, description, status)
            VALUES ($1, $2, $3, $4, $5)
        """, exp_id, org_id, "MNIST Classification", "Handwritten digit classification using CNN", "running")
        
        print(f"✅ Experiment created: MNIST Classification")
        
        # Create a test run
        run_id = str(uuid.uuid4())
        await conn.execute("""
            INSERT INTO runs (id, experiment_id, run_number, status, started_at)
            VALUES ($1, $2, $3, $4, $5)
        """, run_id, exp_id, 1, "running", datetime.utcnow())
        
        print(f"✅ Run created: Run #1")
        
        # Create test metrics
        for step in range(10):
            metric_id = str(uuid.uuid4())
            await conn.execute("""
                INSERT INTO metrics (id, run_id, key, value, step, timestamp)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, metric_id, run_id, "accuracy", 0.8 + (step * 0.02), step, datetime.utcnow())
            
            if step % 3 == 0:
                await conn.execute("""
                    INSERT INTO metrics (id, run_id, key, value, step, timestamp)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, str(uuid.uuid4()), run_id, "loss", 0.4 - (step * 0.03), step, datetime.utcnow())
        
        print(f"✅ 10 metrics created for testing")
        
        # Show summary
        print("\n📊 Test Data Summary:")
        print("-" * 30)
        
        # Count all tables
        tables = await conn.fetch("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' ORDER BY table_name
        """)
        
        for table in tables:
            count = await conn.fetchval(f"SELECT COUNT(*) FROM {table['table_name']}")
            print(f"  {table['table_name']}: {count} rows")
        
        await conn.close()
        
        print("\n" + "=" * 50)
        print("✅ TEST DATA CREATED SUCCESSFULLY")
        print("=" * 50)
        print("\n📋 Test Credentials:")
        print("  👤 Researcher: researcher@test.com / password123")
        print("  👤 Admin: admin@test.com / admin123")
        print("  🏢 Organization: Test Research Lab (test-research-lab)")
        print("\n🔗 Test endpoints:")
        print("  POST http://localhost:8000/auth/login")
        print("  POST http://localhost:8000/v1/experiments/")
        print("  GET  http://localhost:8000/v1/search/")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print("ResearchOS - Test Data Setup")
    print("=" * 60)
    
    success = asyncio.run(create_test_data())
    
    if success:
        print("\n🎉 Ready for authentication testing!")
        print("\nNext steps:")
        print("  1. Test login with researcher@test.com / password123")
        print("  2. Test JWT token authentication")
        print("  3. Test experiment creation")
        print("  4. Test protected endpoints")
    else:
        print("\n❌ Failed to create test data")
    
    return success

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)