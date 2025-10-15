from fastapi import APIRouter, HTTPException, Depends
from typing import List
import logging
from datetime import datetime
import httpx

from app.api.schemas import (
    LookupRequest,
    BatchLookupRequest,
    ServiceResponseSchema,
    BatchResponseSchema,
    HealthResponse
)
from app.controllers.whatsapp_controller import WhatsAppController
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


async def get_controller() -> WhatsAppController:
    """Dependency to get controller instance"""
    from main import app
    return app.state.enhanced_controller


@router.post("/lookup", response_model=ServiceResponseSchema)
async def lookup_profile(
    request: LookupRequest,
    controller: WhatsAppController = Depends(get_controller)
):
    """
    Lookup WhatsApp profile by phone number
    
    Returns profile information including:
    - Existence check
    - Status message
    - Business information
    - Avatar images
    """
    try:
        result = await controller.lookup_profile(request.phone, request.session_id)
        return result
    except Exception as e:
        logger.error(f"Lookup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/controller", response_model=BatchResponseSchema)
async def batch_lookup(
    request: BatchLookupRequest,
    controller: WhatsAppController = Depends(get_controller)
):
    """
    Batch lookup using validator service to determine data types
    
    This endpoint:
    1. Validates input using validator service
    2. Routes to appropriate lookup services
    3. Aggregates results
    """
    results = []
    
    try:
        validated_data = await validate_inputs(request.query)
        
        for item in validated_data:
            item_type = item.get("body", {}).get("type")
            clean_data = item.get("body", {}).get("clean_data")
            
            if item_type == "phone":
                result = await controller.lookup_profile(clean_data, request.session_id)
                results.append(result)
            else:
                logger.info(f"Skipping type: {item_type}")
                results.append({
                    "headers": {"sender": settings.SERVICE_NAME},
                    "body": {"message": f"Type {item_type} not supported"},
                    "extra": item
                })
        
        return {"results": results}
    
    except Exception as e:
        logger.error(f"Batch lookup error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def validate_inputs(query: List[str]) -> List[dict]:
    """Call validator service to identify input types"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                settings.VALIDATOR_URL,
                json={"query": query},
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Validator service error: {e}")
        return [
            {
                "headers": {"sender": "fallback"},
                "body": {"type": "phone", "clean_data": q, "request_data": q},
                "extra": {}
            }
            for q in query
        ]
        
        
@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "timestamp": int(datetime.now().timestamp())
    }
