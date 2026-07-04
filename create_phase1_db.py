#!/usr/bin/env python3
"""
Simple SQL script to create Phase 1 core tables
"""

import psycopg2
import sys

def create_phase1_tables():
    """Create Phase 1 core tables"""
    db_url = "postgresql://researchos:researchos@postgres:5432/researchos"
    
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("Creating Phase 1 tables...")
        
        # Create core enums (simplified)
        cursor.execute("""
            CREATE TYPE node_type AS ENUM (
                'idea', 'hypothesis', 'experiment', 'run', 'paper', 'dataset', 
                'model', 'notebook', 'block', 'citation', 'person', 'organization'
            )
        """)
        print("✓ Created node_type enum")
        
        # Create organizations table
        cursor.execute("""
            CREATE TABLE organizations (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(255) NOT NULL,
                slug VARCHAR(100) UNIQUE NOT NULL,
                plan VARCHAR(50) DEFAULT 'free',
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        print("✓ Created organizations table")
        
        # Create users table
        cursor.execute("""
            CREATE TABLE users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email VARCHAR(255) UNIQUE NOT NULL,
                name VARCHAR(255),
                auth_provider VARCHAR(50) NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        print("✓ Created users table")
        
        # Create organization_members
        cursor.execute("""
            CREATE TABLE organization_members (
                organization_id UUID NOT NULL,
                user_id UUID NOT NULL,
                role VARCHAR(50) DEFAULT 'member',
                joined_at TIMESTAMPTZ DEFAULT NOW(),
                PRIMARY KEY (organization_id, user_id)
            )
        """)
        print("✓ Created organization_members table")
        
        # Create experiments table
        cursor.execute("""
            CREATE TABLE experiments (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                organization_id UUID NOT NULL,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                status VARCHAR(50) DEFAULT 'created',
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        print("✓ Created experiments table")
        
        # Create runs table
        cursor.execute("""
            CREATE TABLE runs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                experiment_id UUID NOT NULL,
                run_number INT NOT NULL,
                status VARCHAR(50) DEFAULT 'created',
                started_at TIMESTAMPTZ,
                ended_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        print("✓ Created runs table")
        
        # Create metrics table (simplified)
        cursor.execute("""
            CREATE TABLE metrics (
                id UUID DEFAULT gen_random_uuid(),
                run_id UUID NOT NULL,
                key VARCHAR(255) NOT NULL,
                value FLOAT NOT NULL,
                step INT DEFAULT 0,
                timestamp TIMESTAMPTZ DEFAULT NOW(),
                PRIMARY KEY (run_id, key, step, timestamp)
            )
        """)
        print("✓ Created metrics table")
        
        # Create indexes
        cursor.execute("CREATE INDEX idx_experiments_org ON experiments(organization_id)")
        cursor.execute("CREATE INDEX idx_runs_experiment ON runs(experiment_id)")
        cursor.execute("CREATE INDEX idx_metrics_run ON metrics(run_id)")
        
        print("\n✅ Phase 1 database created successfully!")
        
        # Verify tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        print(f"\n📊 Tables in database: {len(tables)}")
        for table in tables:
            print(f"  - {table[0]}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_phase1_tables()
    sys.exit(0 if success else 1)