"""Health check endpoints"""
from datetime import datetime

from fastapi import APIRouter, Depends
from infrastructure.database import db as database

router = APIRouter()

async def get_db():
    """Dependency to get database connection"""
    return database

@router.get("/")
async def health():
    """Health check"""
    return {"status": "healthy"}

@router.get("/ready")
async def readiness(
    db = Depends(get_db)
):
    """Readiness check with database connectivity"""

    checks = {}
    all_healthy = True

    # Check database
    try:
        db_status = await db.execute("SELECT 1")
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {str(e)}"
        all_healthy = False

    # Check pgvector extension (verify embeddings work)
    try:
        vector_test = await db.fetch_one("SELECT '[1,2,3]'::vector - '[0,0,0]'::vector as distance")
        checks["pgvector"] = "healthy" if vector_test else "unhealthy"
    except Exception as e:
        checks["pgvector"] = f"unhealthy: {str(e)}"
        all_healthy = False

    # Check pg_trgm extension
    try:
        trigram_test = await db.fetch_one("SELECT 'test' % 'test' as similarity")
        checks["pg_trgm"] = "healthy" if trigram_test else "unhealthy"
    except Exception as e:
        checks["pg_trgm"] = f"unhealthy: {str(e)}"
        all_healthy = False

    # Check pg_partman extension
    try:
        partman_test = await db.fetch_one("SELECT 1 FROM pg_extension WHERE extname = 'pg_partman'")
        checks["pg_partman"] = "healthy" if partman_test else "unhealthy"
    except Exception as e:
        checks["pg_partman"] = f"unhealthy: {str(e)}"
        all_healthy = False

    # Check sample data
    try:
        org_count = await db.fetch_one("SELECT COUNT(*) as count FROM organizations")
        checks["sample_data"] = "healthy" if org_count["count"] > 0 else "unhealthy"
    except Exception as e:
        checks["sample_data"] = f"unhealthy: {str(e)}"
        all_healthy = False

    status = "ready" if all_healthy else "not_ready"

    return {
        "status": status,
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }
