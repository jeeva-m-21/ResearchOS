"""FastAPI application entry point"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from prometheus_client import make_asgi_app

from .routes import auth, experiments, search, health, metrics, events
from .middleware.auth import AuthMiddleware, OrganizationMiddleware
from src.infrastructure.database import db

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager for startup/shutdown"""
    # Startup: Connect to database
    database_url = os.getenv("DATABASE_URL", "postgresql://researchos:researchos@postgres:5432/researchos")
    await db.connect(database_url)
    print(f"✅ Database connected: {database_url}")
    
    yield
    
    # Shutdown: Disconnect from database
    await db.disconnect()
    print("✅ Database disconnected")

app = FastAPI(
    title="ResearchOS API",
    description="Research Operating System API",
    version="1.0.0",
    lifespan=lifespan,
)

# Middleware
app.add_middleware(AuthMiddleware)
app.add_middleware(OrganizationMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(experiments.router, prefix="/v1/experiments", tags=["Experiments"])
app.include_router(search.router, prefix="/v1/search", tags=["Search"])
app.include_router(metrics.router, prefix="/v1", tags=["Metrics"])
app.include_router(events.router, prefix="/v1", tags=["Events"])

# Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
