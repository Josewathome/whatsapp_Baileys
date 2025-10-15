# ============================================================================
# File: api/session_routes.py
# ============================================================================
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging

from app.controllers.enhanced_whatsapp_controller import EnhancedWhatsAppController
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/session", tags=["session"])


class RegistrationStartResponse(BaseModel):
    session_id: str
    qr_code: str
    status: str


class RegistrationCompleteRequest(BaseModel):
    session_id: str
    phone_number: str





async def get_enhanced_controller() -> EnhancedWhatsAppController:
    """Dependency to get enhanced controller"""
    from main import app
    return app.state.enhanced_controller

from app.infrastructure.encryption.encrypt import encrypt_for_url, decrypt_from_url

@router.post("/start-registration")
async def start_registration(
    controller: EnhancedWhatsAppController = Depends(get_enhanced_controller)
):
    """Start new WhatsApp session registration"""
    try:
        result = await controller.start_registration()
        qr_code_value = encrypt_for_url(result['qr_code'])
        
        URL_Modified = f"{settings.BASE_URL}/api/{settings.VERSION_VALUE}/qrcode?data={qr_code_value}"
        
        result['url_path'] = URL_Modified
        return [
            {
                    "headers": {"sender": settings.SERVICE_NAME},
                    "body": {"message": result},
                    "extra": {}
                }
        ]
    except Exception as e:
        logger.error(f"Registration start failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/complete-registration")
async def complete_registration(
    request: RegistrationCompleteRequest,
    controller: EnhancedWhatsAppController = Depends(get_enhanced_controller)
):
    """Complete session registration with phone number"""
    try:
        success = await controller.complete_registration(
            request.session_id,
            request.phone_number
        )
        
        return [
                {
                        "headers": {"sender": settings.SERVICE_NAME},
                        "body": {"success": success,
                                "message": "Registration completed" if success else "Registration failed"
                                    },
                        "extra": {}
                    }
            ]
    
    except Exception as e:
        logger.error(f"Registration completion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_connection_status(
    controller: EnhancedWhatsAppController = Depends(get_enhanced_controller)
):
    """Get current connection and session status"""
    try:
        connection_state = controller.connection_manager.get_state()
        health_status = controller.health_monitor.is_healthy()
        
        return [
                    {
                            "headers": {"sender": settings.SERVICE_NAME},
                            "body": {
                                    "state": connection_state.value,
                                    "pod": controller.pod_name,
                                    "session_phone": controller.current_session.get("phone") if controller.current_session else None,
                                    "uptime": controller.health_monitor.get_uptime(),
                                    "healthy": health_status
                                        },
                            "extra": {}
                        }
                ]
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restart")
async def restart_connection(
    controller: EnhancedWhatsAppController = Depends(get_enhanced_controller)
):
    """Restart connection"""
    try:
        success = await controller.initialize()
        return [
                {
                        "headers": {"sender": settings.SERVICE_NAME},
                        "body": {"success": success,
                                "message": "Connection restarted" if success else "Restart failed"
                                    },
                        "extra": {}
                    }
            ]
    
    except Exception as e:
        logger.error(f"Restart failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))