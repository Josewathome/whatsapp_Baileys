import logging
from app.domain.exceptions import AccountLockedException

logger = logging.getLogger(__name__)


class ExistsService:
    """Check if WhatsApp account exists"""
    
    def __init__(self, whatsapp_client):
        self.client = whatsapp_client
    
    async def check_exists(self, phone: str) -> dict:
        """Check if phone number has WhatsApp account"""
        try:
            jid = f"{phone}@c.us"
            result = await self.client.on_whatsapp(jid)
            
            exists = result and result[0].get("exists", False) if result else False
            
            return {"is_exists": exists}
        
        except Exception as e:
            self._check_account_errors(e)
            raise
    
    @staticmethod
    def _check_account_errors(error: Exception):
        """Check for account-related errors"""
        error_str = str(error)
        if "Connection Closed" in error_str or "Session is invalid" in error_str:
            raise AccountLockedException("Account is locked")