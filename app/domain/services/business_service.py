import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class BusinessService:
    """Retrieve WhatsApp Business profile information"""
    
    DAY_TRANSLATION = {
        "mon": "Пн", "tue": "Вт", "wed": "Ср", "thu": "Чт",
        "fri": "Пт", "sat": "Сб", "sun": "Вс"
    }
    
    MODE_TRANSLATION = {
        "appointment_only": "Только по записи",
        "open_24h": "Круглосуточно",
        "closed": "Закрыто"
    }
    
    def __init__(self, whatsapp_client):
        self.client = whatsapp_client
    
    async def get_business_info(self, phone: str) -> dict:
        """Get business profile information"""
        try:
            jid = f"{phone}@c.us"
            result = await self.client.get_business_profile(jid)
            
            if not result:
                return {"is_business": False}
            
            output = {"is_business": True}
            
            field_mapping = {
                "address": "business_address",
                "description": "business_description",
                "category": "business_category",
                "email": "business_email"
            }
            
            for src, dst in field_mapping.items():
                if result.get(src):
                    output[dst] = result[src]
            
            if isinstance(result.get("website"), list):
                output["business_websites"] = result["website"]
            
            if result.get("business_hours"):
                schedule_data = self._format_schedule(result["business_hours"])
                output.update(schedule_data)
            
            return output
        
        except Exception as e:
            logger.warning(f"Error getting business info: {e}")
            return {"is_business": False}
    
    def _format_schedule(self, hours: dict) -> dict:
        """Format business hours schedule"""
        output = {
            "business_timezone": hours.get("timezone", ""),
            "business_schedule": ""
        }
        
        config = hours.get("business_config") or hours.get("config", [])
        
        for day_code, day_name in self.DAY_TRANSLATION.items():
            period = next((d for d in config if d.get("day_of_week") == day_code), None)
            
            if period:
                open_time = self._format_time(period.get("open_time"))
                close_time = self._format_time(period.get("close_time"))
                mode = period.get("mode")
                
                if mode and mode in self.MODE_TRANSLATION:
                    interval = self.MODE_TRANSLATION[mode]
                else:
                    interval = f"{open_time or '??'} - {close_time or '??'}"
                
                output["business_schedule"] += f"{day_name}: {interval}\n"
        
        return output
    
    @staticmethod
    def _format_time(minutes: Optional[int]) -> Optional[str]:
        if minutes is None:
            return None
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours:02d}:{mins:02d}"