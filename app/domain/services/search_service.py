import logging
from typing import Dict, Any
from datetime import datetime
import asyncio
from app.domain.exceptions import NoDataError

logger = logging.getLogger(__name__)


class SearchService:
    """Orchestrate profile search across multiple services"""
    
    def __init__(self, exists_service, status_service, business_service, avatar_service):
        self.exists_service = exists_service
        self.status_service = status_service
        self.business_service = business_service
        self.avatar_service = avatar_service
    
    async def search_profile(self, phone: str, session_id: str) -> dict:
        """Search for WhatsApp profile information"""
        start_time = datetime.now()
        logger.info(f"Starting profile search for: {phone}")
        
        exists_result = await self.exists_service.check_exists(phone, session_id)
        
        if not exists_result.get("is_exists", False):
            logger.info(f"User doesn't exist: {phone}")
            raise NoDataError("User not found")
        print("Get status uses url baileys-service for = fetchStatus")
        status_task = self.status_service.get_status(phone,session_id)
        print(f"fetch status Done")
        
        print("Get getBusinessProfile uses url baileys-service for = getBusinessProfile")
        business_task = self.business_service.get_business_info(phone,session_id)
        print(f"fetch business Done")
        
        print("Get image avatar preview uses url baileys-service for = profile_picture_url")
        avatar_preview_task = self.avatar_service.get_avatar(phone,session_id, format="preview")
        print(f"fetch privew image done")
        
        print("Get image avatar full uses url baileys-service for = profile_picture_url")
        avatar_full_task = self.avatar_service.get_avatar(phone,session_id, format="image")
        print(f"fetch full image Done ")
        results = await asyncio.gather(
            status_task,
            business_task,
            avatar_preview_task,
            avatar_full_task,
            return_exceptions=True
        )
        
        status_result, business_result, avatar_preview, avatar_full = results
        
        profile_data = {
            "result_code": "FOUND",
            "phone": phone,
            "is_exists": True,
            **self._safe_dict(status_result),
            **self._safe_dict(business_result),
            **self._safe_dict(avatar_preview),
            **self._safe_dict(avatar_full)
        }
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"Profile search completed in {elapsed:.2f}s")
        
        return profile_data
    
    @staticmethod
    def _safe_dict(result: Any) -> dict:
        if isinstance(result, Exception):
            logger.warning(f"Service error: {result}")
            return {}
        return result if isinstance(result, dict) else {}
