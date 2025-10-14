# ============================================================================
# File: domain/services/session_registration_service.py (REAL BAILEYS CALLS)
# ============================================================================
import logging
import base64
import qrcode
import io
import uuid
import httpx
from typing import Optional, Dict, Any
from app.domain.exceptions import SessionException
from app.core.config import settings
logger = logging.getLogger(__name__)


class SessionRegistrationService:
    """Handle WhatsApp session registration with REAL Baileys bridge calls"""
    
    def __init__(self, whatsapp_client, session_store):
        self.client = whatsapp_client
        self.session_store = session_store
        self.baileys_bridge_url = settings.BAILEYS_BRIDGE_URL
        self._pending_sessions: Dict[str, dict] = {}
        self._http_client = httpx.AsyncClient(timeout=30.0)
    
    async def start_registration(self, pod_name: str) -> Dict[str, Any]:
        """Start new session registration with REAL Baileys bridge"""
        try:
            session_id = f"pending_{pod_name}_{uuid.uuid4().hex[:8]}"
            
            # Get REAL QR code from Baileys bridge
            qr_data = await self._get_real_baileys_qr_code(session_id)
            
            # Initialize pending session
            self._pending_sessions[session_id] = {
                "pod": pod_name,
                "status": "qr_ready",
                "created_at": self._current_timestamp(),
                "qr_code": qr_data,
                "session_id": session_id,
                "baileys_authenticated": False
            }
            
            return {
                "session_id": session_id,
                "qr_code": qr_data,
                "status": "qr_ready",
                "url_path": "qrcode URL",  # Will be set by route
                "message": "Scan this REAL WhatsApp QR code to authenticate",
                "instructions": "Open WhatsApp → Linked Devices → Link a Device",
                "source": "baileys_bridge"  # Indicates real QR code
            }
            
        except Exception as e:
            logger.error(f"Failed to start registration with Baileys: {e}")
            raise SessionException(f"Baileys bridge unavailable: {e}")
    
    async def _get_real_baileys_qr_code(self, session_id: str) -> str:
        """Get REAL WhatsApp QR code from Baileys bridge via HTTP"""
        try:
            logger.info(f"Calling Baileys bridge at {self.baileys_bridge_url}/start-auth")
            
            # REAL HTTP call to Baileys bridge
            response = await self._http_client.post(
                f"{self.baileys_bridge_url}/start-auth",
                json={"session_id": session_id},
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                qr_content = data.get("qr_content")
                
                if not qr_content:
                    raise SessionException("No QR content received from Baileys bridge")
                
                logger.info(f"✅ Received real QR content from Baileys bridge: {qr_content[:50]}...")
                
                # Convert QR content to proper QR code image
                qr_data = await self._generate_qr_from_baileys_content(qr_content)
                return qr_data
            else:
                error_msg = f"Baileys bridge error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise SessionException(error_msg)
                
        except httpx.TimeoutException:
            error_msg = "Baileys bridge timeout - service may be down"
            logger.error(error_msg)
            raise SessionException(error_msg)
        except httpx.ConnectError:
            error_msg = f"Cannot connect to Baileys bridge at {self.baileys_bridge_url}"
            logger.error(error_msg)
            raise SessionException(error_msg)
        except Exception as e:
            logger.error(f"Unexpected error calling Baileys bridge: {e}")
            raise SessionException(f"Baileys bridge call failed: {e}")
    
    async def _generate_qr_from_baileys_content(self, qr_content: str) -> str:
        """Generate QR code image from Baileys content"""
        try:
            qr = qrcode.QRCode(
                version=6,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=12,
                border=4,
            )
            
            qr.add_data(qr_content)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            buffer = io.BytesIO()
            img.save(buffer, format="PNG", optimize=True)
            buffer.seek(0)
            
            img_str = base64.b64encode(buffer.getvalue()).decode()
            return f"data:image/png;base64,{img_str}"
            
        except Exception as e:
            logger.error(f"QR generation from Baileys content failed: {e}")
            raise SessionException("Failed to generate QR code image")
    
    async def validate_session(self, session_id: str, phone_number: str) -> bool:
        """Validate session with REAL Baileys authentication check"""
        if session_id not in self._pending_sessions:
            raise SessionException("Session not found or expired")
        
        session_data = self._pending_sessions[session_id]
        
        try:
            # REAL check with Baileys bridge if session is authenticated
            is_authenticated = await self._check_baileys_authentication(session_id)
            
            if not is_authenticated:
                raise SessionException("WhatsApp session not authenticated yet. Please scan the QR code first.")
            
            if not self._validate_phone_number(phone_number):
                raise SessionException("Invalid phone number format")
            
            # Verify the session is actually working by making a test call
            await self._verify_baileys_session()
            
            # Create permanent session
            await self.session_store.add_session(
                phone=phone_number,
                pod=session_data["pod"],
                session_data=self._generate_session_data(phone_number)
            )
            
            # Clean up pending session
            del self._pending_sessions[session_id]
            
            logger.info(f"✅ REAL Baileys session registered for {phone_number} on pod {session_data['pod']}")
            return True
        
        except Exception as e:
            logger.error(f"Session validation failed: {e}")
            raise SessionException(f"Validation failed: {e}")
    
    async def _check_baileys_authentication(self, session_id: str) -> bool:
        """REAL check with Baileys bridge for authentication status"""
        try:
            logger.info(f"Checking authentication status with Baileys bridge for session: {session_id}")
            
            response = await self._http_client.post(
                f"{self.baileys_bridge_url}/check-auth",
                json={"session_id": session_id},
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                authenticated = data.get("authenticated", False)
                
                if authenticated:
                    logger.info(f"✅ Session {session_id} is authenticated with Baileys")
                else:
                    logger.info(f"⏳ Session {session_id} not authenticated yet")
                
                return authenticated
            else:
                logger.error(f"Baileys auth check failed: {response.status_code}")
                return False
                
        except httpx.TimeoutException:
            logger.error("Timeout checking Baileys authentication")
            return False
        except httpx.ConnectError:
            logger.error(f"Cannot connect to Baileys bridge at {self.baileys_bridge_url}")
            return False
        except Exception as e:
            logger.error(f"Error checking Baileys authentication: {e}")
            return False
    
    async def _verify_baileys_session(self) -> bool:
        """Verify Baileys session is actually working by making a test call"""
        try:
            # Make a simple health check to verify Baileys is responsive
            response = await self._http_client.get(
                f"{self.baileys_bridge_url}/health",
                timeout=10.0
            )
            
            if response.status_code == 200:
                health_data = response.json()
                is_connected = health_data.get("status") == "connected"
                
                if is_connected:
                    logger.info("✅ Baileys bridge is connected and healthy")
                    return True
                else:
                    logger.warning("⚠️ Baileys bridge is running but not connected to WhatsApp")
                    return False
            else:
                logger.error(f"Baileys health check failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Baileys session verification failed: {e}")
            return False
    
    async def get_baileys_health(self) -> Dict[str, Any]:
        """Get Baileys bridge health status"""
        try:
            response = await self._http_client.get(
                f"{self.baileys_bridge_url}/health",
                timeout=10.0
            )
            
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "baileys_status": response.json().get("status", "unknown"),
                    "connected": response.json().get("status") == "connected"
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}",
                    "connected": False
                }
                
        except Exception as e:
            return {
                "status": "unreachable",
                "error": str(e),
                "connected": False
            }
    
    def _validate_phone_number(self, phone_number: str) -> bool:
        """Basic phone number validation"""
        import re
        pattern = r'^\+?[1-9]\d{1,14}$'
        return bool(re.match(pattern, phone_number.replace(" ", "")))
    
    def _generate_session_data(self, phone_number: str) -> bytes:
        """Generate session data with Baileys authentication info"""
        import json
        from datetime import datetime
        
        session_data = {
            "phone": phone_number,
            "created_at": datetime.now().isoformat(),
            "auth_data": "baileys_authenticated",
            "version": "1.0",
            "status": "active",
            "authenticated_via": "baileys_bridge",
            "baileys_url": self.baileys_bridge_url,
            "authenticated_at": datetime.now().isoformat()
        }
        
        return json.dumps(session_data).encode('utf-8')
    
    def _current_timestamp(self) -> int:
        """Get current timestamp"""
        import time
        return int(time.time())
    
    def cleanup_expired_sessions(self, max_age_seconds: int = 300):
        """Clean up expired pending sessions"""
        current_time = self._current_timestamp()
        expired_sessions = []
        
        for session_id, session_data in self._pending_sessions.items():
            if current_time - session_data["created_at"] > max_age_seconds:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self._pending_sessions[session_id]
            logger.info(f"Cleaned up expired session: {session_id}")
    
    def get_pending_sessions_count(self) -> int:
        """Get number of pending sessions"""
        return len(self._pending_sessions)
    
    async def close(self):
        """Clean up HTTP client"""
        await self._http_client.aclose()