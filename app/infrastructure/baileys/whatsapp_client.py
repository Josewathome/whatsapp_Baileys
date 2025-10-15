import logging
import httpx
from typing import Optional, Dict, Any, List
from app.core.config import settings

logger = logging.getLogger(__name__)


class WhatsAppClient:
    """
    Client for communicating with Baileys bridge service
    
    This communicates with a Node.js service running Baileys
    """
    
    def __init__(self, base_url: str):
        self.base_url = settings.BAILEYS_BRIDGE_URL
        self.timeout = httpx.Timeout(30.0)
    
    async def on_whatsapp(self, jid: str, session_id: str) -> List[Dict[str, Any]]:
        """Check if JID exists on WhatsApp"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/onWhatsApp",
                    json={"jid": jid, "session_id":session_id}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error in onWhatsApp: {e}")
            raise
    
    async def fetch_status(self, jid: str, session_id: str) -> Optional[Dict[str, Any]]:
        """Fetch status message"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/fetchStatus",
                    json={"jid": jid, "session_id":session_id}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error in fetchStatus: {e}")
            raise
    
    async def get_business_profile(self, jid: str, session_id: str) -> Optional[Dict[str, Any]]:
        """Get business profile"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/getBusinessProfile",
                    json={"jid": jid, "session_id":session_id}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error in getBusinessProfile: {e}")
            raise
    
    async def profile_picture_url(self, jid: str,session_id: str, format: str) -> Optional[str]:
        """Get profile picture URL"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/profilePictureUrl",
                    json={"jid": jid,"session_id":session_id, "format": format}
                )
                response.raise_for_status()
                return response.json().get("url")
        except Exception as e:
            logger.error(f"Error in profilePictureUrl: {e}")
            raise