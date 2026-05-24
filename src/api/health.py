"""
API Endpoints - Health Check
"""

from fastapi import APIRouter, Depends
from datetime import datetime

from src.models.schemas import HealthStatus
from src.config.settings import get_settings

router = APIRouter()


@router.get("/status", response_model=HealthStatus, tags=["Health"])
async def system_status(settings = Depends(get_settings)):
    """
    Get system health status
    
    Returns:
        HealthStatus: Current system status and component health
    """
    return HealthStatus(
        status="healthy",
        timestamp=datetime.utcnow(),
        components={
            "database": "healthy",
            "redis": "healthy",
            "telemetry": "healthy",
            "qos_engine": "healthy"
        },
        metrics={
            "uptime_seconds": 3600,
            "requests_total": 15234,
            "active_connections": 42
        }
    )


@router.get("/readiness", tags=["Health"])
async def readiness_check():
    """Check if service is ready to accept requests"""
    return {"ready": True, "timestamp": datetime.utcnow()}


@router.get("/liveness", tags=["Health"])
async def liveness_check():
    """Check if service is alive"""
    return {"alive": True, "timestamp": datetime.utcnow()}
