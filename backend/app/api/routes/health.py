"""
Health check endpoint for THERMALIFT API.
"""
from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Service status and data policy information.
    """
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "data_policy": "SYNTHETIC/DEMO",
        "version": "1.0.0"
    }