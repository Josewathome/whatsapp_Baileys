from typing import Optional, Dict
from asyncio import Queue, Lock
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class InMemoryQueue:
    """In-memory queue replacing KeyDB/Redis"""
    
    def __init__(self, queue_name: str, expire_time: int = 600):
        self._queue = Queue()
        self._registry: Dict[str, dict] = {}
        self._lock = Lock()
        self._queue_name = queue_name
        self._expire_time = expire_time
    
    async def add_task(self, phone_number: str) -> None:
        """Add task to queue"""
        await self._queue.put(phone_number)
        logger.info(f"Added task: {phone_number}")
    
    async def check_queue(self) -> Optional[str]:
        """Get next task from queue"""
        if self._queue.empty():
            return None
        
        phone = await self._queue.get()
        
        async with self._lock:
            if phone in self._registry:
                entry = self._registry[phone]
                if entry.get("code", 0) >= 200 and entry.get("code", 0) < 300:
                    return None
        
        logger.info(f"Processing task: {phone}")
        return phone
    
    async def set_answer(self, phone_number: str, response: dict) -> None:
        """Store response with TTL"""
        async with self._lock:
            self._registry[phone_number] = {
                **response,
                "timestamp": datetime.now()
            }
        logger.info(f"Stored answer for: {phone_number}")
    
    async def return_to_queue(self, phone_number: str) -> None:
        """Return task to queue"""
        await self._queue.put(phone_number)
        logger.info(f"Returned to queue: {phone_number}")