import logging
from typing import Optional, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class StatusService:
    """Retrieve WhatsApp status information"""
    
    def __init__(self, whatsapp_client):
        self.client = whatsapp_client
    
    async def get_status(self, phone: str) -> dict:
        """Get status message and metadata"""
        try:
            jid = f"{phone}@c.us"
            result = await self.client.fetch_status(jid)
            
            if not result:
                return {"status_hidden": False}
            
            output = {"status_hidden": False}
            
            if result.get("status"):
                output["status"] = result["status"]
            
            if result.get("setAt"):
                set_at = result["setAt"]
                if "Invalid" not in str(set_at):
                    output["status_set_at"] = set_at if isinstance(set_at, str) else set_at.isoformat()
            
            return output
        
        except Exception as e:
            if self._is_hidden_error(e):
                return {"status_hidden": True}
            logger.warning(f"Error getting status: {e}")
            return {"status_hidden": False}
    
    @staticmethod
    def _is_hidden_error(error: Exception) -> bool:
        error_str = str(error)
        return "not-authorized" in error_str or "Cannot read properties of undefined" in error_str