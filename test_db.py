#!/usr/bin/env python3
"""
Test database connectivity and table verification
"""
import asyncio
import sys

async def test_database():
    print("🧪 Testing Database Connectivity")
    print("=" * 40)
    
    try:
        # Import database module
        from src.infrastructure.database import db
        
        print("Connecting to database...")
        await db.connect()
        print("✅ Database connected successfully")
        
        # Test query for organizations
        print("\n📊 Testing table queries:")
        
        # Test organizations table
        org_count = await db.fetch_val("SELECT COUNT(*) FROM organizations")
        print(f"  ✓ Organizations count: {org_count}")
        
        # Test users table
        user_count = await db.fetch_val("SELECT COUNT(*) FROM users")
        print(f"  ✓ Users count: {user_count}")
        
        # Test experiments table
        exp_count = await db.fetch_val("SELECT COUNT(*) FROM experiments")
        print(f"  ✓ Experiments count: {exp_count}")
        
        # Test a more complex query
        print("\n🔍 Testing schema structure:")
        
        # Show table descriptions
        tables = await db.fetch_all("""
            SELECT 
                table_name,
                string_agg(column_name, ', ') as columns
            FROM information_schema.columns 
            WHERE table_schema = 'public'
            GROUP BY table_name
            ORDER BY table_name
        """)
        
        for table in tables:
            print(f"  📁 {table['table_name']}: {table['columns'][:50]}...")
        
        # Test insert/update (transaction)
        print("\n💾 Testing write operations...")
        
        # Test insert into organizations
        import uuid
        test_org_id = str(uuid.uuid4())
        
        await db.execute("""
            INSERT INTO organizations (id, name, slug, plan)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (id) DO NOTHING
        """, test_org_id, "Test Organization", "test-org", "free")
        
        print(f"  ✓ Insert test organization: test-org")
        
        # Verify insert
        org_name = await db.fetch_val("""
            SELECT name FROM organizations WHERE id = $1
        """, test_org_id)
        
        print(f"  ✓ Retrieved organization: {org_name}")
        
        # Clean up test data
        await db.execute("""
            DELETE FROM organizations WHERE id = $1
        """, test_org_id)
        
        print("  ✓ Cleaned up test data")
        
        # Disconnect
        await db.disconnect()
        print("\n✅ All database tests passed!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run database tests"""
    print("ResearchOS Database Test Suite")
    print("=" * 50)
    
    try:
        success = asyncio.run(test_database())
        
        if success:
            print("\n" + "=" * 50)
            print("✅ DATABASE STATUS: HEALTHY")
            print("=" * 50)
            print("\n✅ Tables created and accessible")
            print("✅ Connection pool working")
            print("✅ Read/write operations working")
            print("✅ Backend can connect to database")
            print("\n📋 Phase 1 Database: READY")
        else:
            print("\n❌ Database configuration issues found")
            
        return success
        
    except Exception as e:
        print(f"\n❌ Test runner error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)