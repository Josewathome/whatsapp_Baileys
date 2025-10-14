# ============================================================================
# File: domain/services/connection_manager.py (FIXED - No External Dependencies)
# ============================================================================
import logging
import asyncio
from typing import Dict, Any, Optional, Callable
from enum import Enum
from app.domain.exceptions import SessionException, AccountLockedException

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    CLOSED = "closed"
    ERROR = "error"


class ConnectionManager:
    """Manage WebSocket connection lifecycle and state"""
    
    def __init__(self, whatsapp_client, session_store):
        self.client = whatsapp_client
        self.session_store = session_store
        self._state: ConnectionState = ConnectionState.DISCONNECTED
        self._event_handlers: Dict[str, list] = {}
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 5
        self._reconnect_delay = 5  # seconds
    
    async def initialize_connection(self, phone: str, pod: str) -> bool:
        """Initialize and establish connection"""
        try:
            self._set_state(ConnectionState.CONNECTING)
            
            # Get session data
            session = await self.session_store.get_session(pod, ignore_lock=True)
            if not session:
                logger.error(f"No session found for pod {pod}")
                self._set_state(ConnectionState.ERROR)
                return False
            
            # Simulate connection establishment
            connection_result = await self._simulate_connection(session)
            
            if connection_result:
                self._set_state(ConnectionState.CONNECTED)
                self._reconnect_attempts = 0
                logger.info(f"Connection established for {phone}")
                return True
            else:
                self._set_state(ConnectionState.ERROR)
                return False
        
        except Exception as e:
            logger.error(f"Connection initialization failed: {e}")
            self._set_state(ConnectionState.ERROR)
            return False
    
    async def handle_connection_update(self, update_data: Dict[str, Any]):
        """Handle connection state updates"""
        try:
            connection_status = update_data.get("connection", "unknown")
            last_disconnect = update_data.get("lastDisconnect")
            
            logger.info(f"Connection update: {connection_status}")
            
            if connection_status == "connecting":
                self._set_state(ConnectionState.CONNECTING)
                self._emit("connecting", update_data)
            
            elif connection_status == "open":
                self._set_state(ConnectionState.CONNECTED)
                self._reconnect_attempts = 0
                self._emit("connected", update_data)
            
            elif connection_status == "close":
                await self._handle_connection_close(last_disconnect)
            
            else:
                logger.warning(f"Unhandled connection status: {connection_status}")
                self._emit("unhandled", update_data)
        
        except Exception as e:
            logger.error(f"Error handling connection update: {e}")
    
    async def _handle_connection_close(self, last_disconnect: Optional[Dict]):
        """Handle connection close with error code analysis"""
        error_code = self._extract_error_code(last_disconnect)
        
        logger.warning(f"Connection closed with code {error_code}")
        
        if error_code == 401:
            # Logged out
            await self._handle_logout()
        elif error_code == 402:
            # Possible ban
            await self._handle_ban()
        elif error_code == 408:
            # Connection timeout
            await self._handle_timeout()
        elif error_code == 440:
            # Session conflict
            await self._handle_conflict()
        elif error_code in [515, 503, 428]:
            # Restart required
            await self._handle_restart_required()
        else:
            # Generic disconnect
            await self._handle_generic_disconnect()
    
    def _extract_error_code(self, last_disconnect: Optional[Dict]) -> Optional[int]:
        """Extract error code from disconnect payload"""
        if not last_disconnect:
            return None
        
        try:
            # Handle different error formats
            if isinstance(last_disconnect, dict):
                error = last_disconnect.get("error", {})
                if isinstance(error, dict):
                    return error.get("statusCode")
                elif hasattr(error, 'statusCode'):
                    return error.statusCode
            
            return None
        except Exception:
            return None
    
    async def _handle_logout(self):
        """Handle logout event"""
        self._set_state(ConnectionState.CLOSED)
        self._emit("logout", {"reason": "logged_out"})
        logger.error("Session logged out")
        raise AccountLockedException("Session logged out")
    
    async def _handle_ban(self):
        """Handle possible ban"""
        self._set_state(ConnectionState.ERROR)
        self._emit("ban", {"reason": "possible_ban"})
        logger.warning("Possible ban detected")
    
    async def _handle_timeout(self):
        """Handle timeout issues"""
        self._set_state(ConnectionState.ERROR)
        self._emit("timeout", {"reason": "connection_timeout"})
        logger.warning("Connection timeout")
    
    async def _handle_conflict(self):
        """Handle session conflict"""
        self._set_state(ConnectionState.ERROR)
        self._emit("conflict", {"reason": "session_conflict"})
        logger.warning("Session conflict detected")
    
    async def _handle_restart_required(self):
        """Handle restart requirement"""
        self._set_state(ConnectionState.ERROR)
        self._emit("restart", {"reason": "restart_required"})
        logger.info("Restart required")
        await self._attempt_reconnect()
    
    async def _handle_generic_disconnect(self):
        """Handle generic disconnect with reconnect logic"""
        self._set_state(ConnectionState.DISCONNECTED)
        self._emit("disconnected", {"reason": "generic_disconnect"})
        await self._attempt_reconnect()
    
    async def _attempt_reconnect(self):
        """Attempt to reconnect with exponential backoff"""
        if self._reconnect_attempts >= self._max_reconnect_attempts:
            logger.error("Max reconnection attempts reached")
            self._set_state(ConnectionState.ERROR)
            self._emit("reconnect_failed", {"attempts": self._reconnect_attempts})
            return
        
        self._reconnect_attempts += 1
        delay = self._reconnect_delay * self._reconnect_attempts
        
        logger.info(f"Attempting reconnect in {delay}s (attempt {self._reconnect_attempts})")
        await asyncio.sleep(delay)
        
        self._emit("reconnect_attempt", {
            "attempt": self._reconnect_attempts,
            "delay": delay
        })
    
    async def _simulate_connection(self, session_data: Dict) -> bool:
        """Simulate connection establishment"""
        try:
            logger.info("Simulating connection establishment")
            await asyncio.sleep(0.5)  # Simulate connection time
            return True  # Always succeed in simulation
        except Exception as e:
            logger.error(f"Connection simulation failed: {e}")
            return False
    
    def on(self, event: str, handler: Callable):
        """Register event handler"""
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)
    
    def _emit(self, event: str, data: Dict):
        """Emit event to registered handlers"""
        if event in self._event_handlers:
            for handler in self._event_handlers[event]:
                try:
                    handler(data)
                except Exception as e:
                    logger.error(f"Error in event handler for {event}: {e}")
    
    def _set_state(self, state: ConnectionState):
        """Update connection state"""
        old_state = self._state
        self._state = state
        logger.info(f"Connection state changed: {old_state.value} -> {state.value}")
        self._emit("state_change", {
            "old_state": old_state.value,
            "new_state": state.value
        })
    
    def get_state(self) -> ConnectionState:
        """Get current connection state"""
        return self._state
    
    async def close_connection(self):
        """Gracefully close connection"""
        self._set_state(ConnectionState.CLOSED)
        logger.info("Connection closed gracefully")
        self._emit("closed", {"reason": "manual_close"})