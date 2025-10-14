import logging
import aiohttp
import base64
from typing import Literal, Optional

logger = logging.getLogger(__name__)


class AvatarService:
    """Retrieve WhatsApp profile avatars"""
    
    def __init__(self, whatsapp_client):
        self.client = whatsapp_client
    
    async def get_avatar(self, phone: str, format: Literal["preview", "image"] = "preview", 
                        download: bool = False) -> dict:
        """Get avatar URL and optionally download as base64"""
        try:
            jid = f"{phone}@c.us"
            url = await self.client.profile_picture_url(jid, format)
            
            if not url:
                return {"has_avatar": False, "avatar_hidden": False}
            
            output = {
                "has_avatar": True,
                "avatar_hidden": False,
                f"{format}_url": url
            }
            
            if download:
                base64_data = await self._download_image(url)
                if base64_data:
                    output[f"{format}_base64"] = base64_data
            
            return output
        
        except Exception as e:
            if self._is_hidden_error(e):
                return {"avatar_hidden": True, "has_avatar": True}
            if self._is_empty_error(e):
                return {"has_avatar": False, "avatar_hidden": False}
            
            logger.warning(f"Error getting avatar: {e}")
            return {"has_avatar": False, "avatar_hidden": False}
    
    @staticmethod
    async def _download_image(url: str) -> Optional[str]:
        """Download image and convert to base64"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        return None
                    
                    data = await response.read()
                    if len(data) <= 30:
                        logger.warning("Image response too small")
                        return None
                    
                    b64 = base64.b64encode(data).decode('utf-8')
                    return f"data:image/png;base64,{b64}"
        
        except Exception as e:
            logger.error(f"Error downloading image: {e}")
            return None
    
    @staticmethod
    def _is_hidden_error(error: Exception) -> bool:
        error_str = str(error)
        return "not-authorized" in error_str or "Cannot read properties of undefined" in error_str
    
    @staticmethod
    def _is_empty_error(error: Exception) -> bool:
        return "item-not-found" in str(error)