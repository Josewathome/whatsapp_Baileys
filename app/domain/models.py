from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ExistsResponse(BaseModel):
    is_exists: bool


class StatusResponse(BaseModel):
    status_hidden: bool = False
    status: Optional[str] = None
    status_set_at: Optional[str] = None


class AvatarResponse(BaseModel):
    has_avatar: bool = False
    preview_url: Optional[str] = None
    image_url: Optional[str] = None
    preview_base64: Optional[str] = None
    image_base64: Optional[str] = None
    avatar_hidden: bool = False


class BusinessResponse(BaseModel):
    is_business: bool = False
    business_address: Optional[str] = None
    business_description: Optional[str] = None
    business_category: Optional[str] = None
    business_email: Optional[str] = None
    business_websites: Optional[List[str]] = None
    business_timezone: Optional[str] = None
    business_schedule: Optional[str] = None


class ProfileResponse(BaseModel):
    result_code: str = "FOUND"
    phone: str
    is_exists: bool
    status_hidden: Optional[bool] = None
    status: Optional[str] = None
    status_set_at: Optional[str] = None
    is_business: Optional[bool] = None
    business_address: Optional[str] = None
    business_description: Optional[str] = None
    business_category: Optional[str] = None
    business_email: Optional[str] = None
    business_websites: Optional[List[str]] = None
    business_timezone: Optional[str] = None
    business_schedule: Optional[str] = None
    has_avatar: Optional[bool] = None
    preview_url: Optional[str] = None
    image_url: Optional[str] = None
    preview_base64: Optional[str] = None
    image_base64: Optional[str] = None
    avatar_hidden: Optional[bool] = None


class ServiceResponse(BaseModel):
    """Standard service response format"""
    headers: Dict[str, str]
    body: Dict[str, Any]
    extra: Dict[str, Any] = Field(default_factory=dict)