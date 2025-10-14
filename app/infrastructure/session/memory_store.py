from typing import Dict, Optional
from datetime import datetime, timedelta
from asyncio import Lock
import logging

logger = logging.getLogger(__name__)


class InMemorySessionStore:
    """In-memory session storage replacing MongoDB"""
    
    def __init__(self):
        self._sessions: Dict[str, dict] = {}
        self._lock = Lock()
    
    async def add_session(self, phone: str, pod: str, session_data: bytes) -> None:
        """Add new session"""
        async with self._lock:
            session_id = f"{phone}_{pod}"
            self._sessions[session_id] = {
                "phone": phone,
                "pod": pod,
                "session_data": session_data,
                "active": True,
                "count_use": 0,
                "count_success": 0,
                "created": datetime.now(),
                "last_use": None,
                "next_use": None
            }
            logger.info(f"Added session: {session_id}")
    
    async def get_session(self, pod: str, ignore_lock: bool = False) -> Optional[dict]:
        """Get available session for pod"""
        async with self._lock:
            now = datetime.now()
            
            for session_id, session in self._sessions.items():
                if session["pod"] != pod:
                    continue
                if not session["active"]:
                    continue
                if not ignore_lock and session["next_use"] and session["next_use"] > now:
                    continue
                
                session["last_use"] = now
                session["count_use"] += 1
                logger.info(f"Retrieved session: {session_id}")
                return session
            
            return None
    
    async def update_session(self, phone: str, pod: str, **updates) -> None:
        """Update session fields"""
        async with self._lock:
            session_id = f"{phone}_{pod}"
            if session_id in self._sessions:
                self._sessions[session_id].update(updates)
                logger.info(f"Updated session: {session_id}")
    
    async def lock_session(self, phone: str, pod: str, duration_seconds: int) -> None:
        """Lock session for specified duration"""
        next_use = datetime.now() + timedelta(seconds=duration_seconds)
        await self.update_session(phone, pod, next_use=next_use)
    
    async def block_session(self, phone: str, pod: str) -> None:
        """Permanently block session"""
        await self.update_session(phone, pod, active=False)
    
    async def increment_success(self, phone: str, pod: str) -> None:
        """Increment success counter"""
        async with self._lock:
            session_id = f"{phone}_{pod}"
            if session_id in self._sessions:
                self._sessions[session_id]["count_success"] += 1