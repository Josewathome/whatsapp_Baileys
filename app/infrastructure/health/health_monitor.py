# ============================================================================
# File: infrastructure/health/health_monitor.py
# ============================================================================
import logging
import time
import asyncio
from typing import Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class HealthMonitor:
    """Monitor service health and provide liveness information"""
    
    def __init__(self, health_file: str, check_period: int = 60):
        self.health_file = Path(health_file)
        self.check_period = check_period
        self._last_checkpoint = 0
        self._is_healthy = True
        self._startup_time = time.time()
    
    async def checkpoint(self):
        """Update health checkpoint"""
        try:
            self._last_checkpoint = time.time()
            self.health_file.parent.mkdir(parents=True, exist_ok=True)
            self.health_file.write_text(str(int(self._last_checkpoint * 1000)))
            self._is_healthy = True
            logger.debug("Health checkpoint updated")
        except Exception as e:
            logger.error(f"Failed to update health checkpoint: {e}")
            self._is_healthy = False
    
    async def check_health(self, max_period_seconds: int = None) -> bool:
        """Check if service is healthy"""
        if max_period_seconds is None:
            max_period_seconds = self.check_period
        
        try:
            if not self.health_file.exists():
                logger.warning("Health file not found")
                return False
            
            last_time = int(self.health_file.read_text().strip())
            current_time = int(time.time() * 1000)
            diff_seconds = (current_time - last_time) / 1000
            
            is_healthy = diff_seconds <= max_period_seconds
            
            if not is_healthy:
                logger.error(f"Health check failed: last checkpoint {diff_seconds:.1f}s ago")
            
            self._is_healthy = is_healthy
            return is_healthy
        
        except Exception as e:
            logger.error(f"Health check error: {e}")
            self._is_healthy = False
            return False
    
    def is_healthy(self) -> bool:
        """Get current health status"""
        return self._is_healthy
    
    def get_uptime(self) -> float:
        """Get service uptime in seconds"""
        return time.time() - self._startup_time
    
    async def start_health_loop(self):
        """Start background health monitoring"""
        while True:
            try:
                await self.checkpoint()
                await asyncio.sleep(self.check_period // 2)  # Checkpoint twice per period
            except Exception as e:
                logger.error(f"Health loop error: {e}")
                await asyncio.sleep(5)