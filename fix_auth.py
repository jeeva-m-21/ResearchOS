#!/usr/bin/env python3
"""
Fix authentication by creating users that match the expected schema
"""

import asyncio
import uuid
import bcrypt

async def fix_users_schema():
    """Fix user schema and add proper authentication data"""
    
    try:
        import asyncpg
        
        # Database connection
        db_url = "postgresql://researchos:researchos@postgres:5432/researchos"
        conn = await asyncpg.connect(db_url)
        
        print("🔧 Fixing authentication schema...")
        
        # Get the existing test user
        user = await conn.fetchrow("""
            SELECT id, email FROM users WHERE email = 'researcher@test.com'
        """)
        
        if not user:
            print("❌ Test user not found")
            return False
        
        user_id = user['id']
        
        # Create proper bcrypt hash for password
        password = "password123"
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        
        print(f"✅ Generated password hash for {user['email']}")
        
        # Update user with proper password
        await conn.execute("""
            UPDATE users 
            SET password_hash = $1, salt = $2
            WHERE id = $3
        """, password_hash, salt.decode('utf-8'), user_id)
        
        print(f"✅ Updated user {user['email']} with proper password hash")
        
        # Add auth_provider_id
        await conn.execute("""
            UPDATE users 
            SET auth_provider_id = 'email_' || email
            WHERE auth_provider_id IS NULL
        """)
        
        # Check if the query works
        print("\n🧪 Testing database query...")
        test_user = await conn.fetchrow("""
            SELECT id, email, password_hash, name 
            FROM users 
            WHERE email = $1 
            AND deleted_at IS NULL
        """, "researcher@test.com")
        
        if test_user:
            print(f"✅ Query successful for {test_user['email']}")
            print(f"   Has password_hash: {'password_hash' in test_user}")
            
            # Test password verification
            is_correct = bcrypt.checkpw(
                "password123".encode('utf-8'),
                test_user['password_hash'].encode('utf-8')
            )
            
            print(f"✅ Password verification: {is_correct}")
            
        else:
            print("❌ User not found")
        
        # Create test query for logging
        await conn.close()
        
        print("\n" + "=" * 50)
        print("✅ AUTHENTICATION FIXED")
        print("=" * 50)
        print("\n📋 Test Login Credentials:")
        print(f"  Email: researcher@test.com")
        print(f"  Password: password123")
        print(f"  Hashed: ✅")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print("ResearchOS Authentication Fix")
    print("=" * 60)
    
    success = asyncio.run(fix_users_schema())
    
    if success:
        print("\n🎉 Authentication should now work!")
        print("\nTest command:")
        print("  curl -X POST http://localhost:8000/auth/login \\")
        print("    -H 'Content-Type: application/json' \\")
        print("    -d '{\"email\":\"researcher@test.com\",\"password\":\"password123\"}'")
    else:
        print("\n❌ Failed to fix authentication")
    
    return success

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)