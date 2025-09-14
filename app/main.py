"""Main FastAPI application."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
from app.core.config import settings
from app.database.database import engine, Base
from app.api.v1.endpoints import orders, inventory, agents
from app.models.models import *  # Import all models to ensure they're registered


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print("Starting MiniMart AI Inventory Management System...")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")
    
    yield
    
    # Shutdown
    print("Shutting down MiniMart AI Inventory Management System...")


# Create FastAPI application
app = FastAPI(
    title=settings.project_name,
    description="AI-powered inventory management system for mini marts",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(
    orders.router,
    prefix=f"{settings.api_v1_str}/orders",
    tags=["orders"]
)

app.include_router(
    inventory.router,
    prefix=f"{settings.api_v1_str}/inventory",
    tags=["inventory"]
)

app.include_router(
    agents.router,
    prefix=f"{settings.api_v1_str}/agents",
    tags=["agents"]
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to MiniMart AI Inventory Management System",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": "2024-12-19T00:00:00Z",
        "version": "1.0.0"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc),
            "path": str(request.url)
        }
    )


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
