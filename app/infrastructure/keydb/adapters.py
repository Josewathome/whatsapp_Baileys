# ============================================================================
# File: infrastructure/keydb/adapters.py (Updated)
# ============================================================================
from typing import Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ResponseFormatter:
    """Format responses according to specification"""
    
    @staticmethod
    def build_response(code: int = 200, message: str = "ok", 
                      status: str = "ok", data: Any = None) -> dict:
        """Build standard response"""
        return {
            "status": status,
            "code": code,
            "timestamp": int(datetime.now().timestamp()),
            "message": message,
            "data": data or {}
        }
    
    @staticmethod
    def ok(data: Any) -> dict:
        return ResponseFormatter.build_response(200, "ok", "ok", data)
    
    @staticmethod
    def empty() -> dict:
        return ResponseFormatter.build_response(204, "No data", "empty")
    
    @staticmethod
    def error(message: str, code: int = 500) -> dict:
        return ResponseFormatter.build_response(code, str(message), "error")


class ProfileAdapter:
    """Adapt profile data to required format"""
    
    @staticmethod
    def bool_to_russian(value: bool) -> str:
        return "Да" if value else "Нет"
    
    @staticmethod
    def format_profile(profile_data: dict) -> dict:
        """Format profile data to body/extra structure"""
        body = {}
        extra = {}
        
        # Main business fields go in body
        main_fields = [
            "result_code", "phone", "status", "is_business", 
            "has_avatar", "is_exists", "status_hidden", "avatar_hidden"
        ]
        
        for key, value in profile_data.items():
            if value is None:
                continue
            
            # Convert boolean values to Russian
            if isinstance(value, bool):
                value = ProfileAdapter.bool_to_russian(value)
            
            if key in main_fields:
                body[key] = value
            else:
                extra[key] = value
        
        return {"body": body, "extra": extra}
    
    @staticmethod
    def cast_profile_data(profile_data: dict) -> dict:
        """Cast profile data to required format (like original TypeScript version)"""
        if profile_data.get("is_exists"):
            profile_data["result_code"] = "FOUND"
        
        # Convert boolean fields to Russian
        bool_fields = ["is_exists", "is_business", "status_hidden", "avatar_hidden", "has_avatar"]
        for field in bool_fields:
            if field in profile_data:
                profile_data[field] = ProfileAdapter.bool_to_russian(profile_data[field])
        
        return profile_data