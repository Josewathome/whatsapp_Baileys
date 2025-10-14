from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class LookupRequest(BaseModel):
    """Request for profile lookup"""
    phone: str = Field(..., description="Phone number in international format")


class BatchLookupRequest(BaseModel):
    """Batch lookup request"""
    query: List[str] = Field(..., description="List of phone numbers or identifiers")


class ServiceResponseSchema(BaseModel):
    """Standard service response"""
    headers: Dict[str, str]
    body: Dict[str, Any]
    extra: Dict[str, Any] = {}


class BatchResponseSchema(BaseModel):
    """Batch lookup response"""
    results: List[ServiceResponseSchema]


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    timestamp: int