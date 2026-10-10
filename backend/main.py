"""Main application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.db.database import init_db
from app.api import health, auth, engagements, uploads


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for startup and shutdown."""
    # Startup
    print("Initializing database...")
    init_db()
    print("Database initialized successfully")
    yield
    # Shutdown
    print("Application shutting down...")


app = FastAPI(
    title="TRACE - AI-Run Statutory Revenue Audit",
    description="Backend API for evidence-led, reproducible AI-assisted audits",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(engagements.router, prefix="/api/v1/engagements", tags=["engagements"])
app.include_router(uploads.router, prefix="/api/v1/uploads", tags=["uploads"])


@app.get("/")
def read_root():
    return {
        "message": "TRACE Backend API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }