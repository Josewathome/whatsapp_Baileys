# ============================================================================
# File: controllers/whatsapp_controller.py (Enhanced Version)
# ============================================================================
import logging
import asyncio
from typing import Dict
from app.domain.exceptions import NoDataError, AccountLockedException
from app.infrastructure.keydb.adapters import ResponseFormatter, ProfileAdapter
from app.core.config import settings

logger = logging.getLogger(__name__)


class WhatsAppController:
    """Main controller for WhatsApp profile lookup with enhanced features"""
    
    def __init__(
        self,
        search_service,
        session_store,
        queue,
        registration_service=None,
        connection_manager=None,
        health_monitor=None
    ):
        self.search_service = search_service
        self.session_store = session_store
        self.queue = queue
        self.registration_service = registration_service
        self.connection_manager = connection_manager
        self.health_monitor = health_monitor
        
        self.is_running = False
        self.count_reload = 0
        self.count_failures_in_row = 0
    
    async def lookup_profile(self, phone: str) -> dict:
        """Single profile lookup (API endpoint)"""
        try:
            logger.info(f"Looking up profile: {phone}")
            profile_data = await self.search_service.search_profile(phone)
            
            formatted = ProfileAdapter.format_profile(profile_data)
            
            return {
                "headers": {"sender": settings.SERVICE_NAME},
                "body": formatted["body"],
                "extra": formatted["extra"]
            }
        
        except NoDataError as e:
            logger.info(f"No data found: {e}")
            return {
                "headers": {"sender": settings.SERVICE_NAME},
                "body": {"result_code": "NOT_FOUND", "message": "User not found"},
                "extra": {}
            }
        
        except AccountLockedException as e:
            logger.error(f"Account locked: {e}")
            return {
                "headers": {"sender": settings.SERVICE_NAME},
                "body": {"result_code": "ERROR", "message": "Account locked"},
                "extra": {"error": str(e)}
            }
        
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {
                "headers": {"sender": settings.SERVICE_NAME},
                "body": {"result_code": "ERROR", "message": "Internal error"},
                "extra": {"error": str(e)}
            }
    
    async def start_worker(self, pod_name: str):
        """Start background worker for queue processing"""
        logger.info("Worker started. Ready for tasks!")
        self.is_running = True
        
        while self._is_alive():
            try:
                phone_number = await self.queue.check_queue()
                
                if not phone_number:
                    await asyncio.sleep(0.1)
                    continue
                
                logger.info(f"Processing task: {phone_number}")
                
                # Update health checkpoint if available
                if self.health_monitor:
                    await self.health_monitor.checkpoint()
                
                session = await self.session_store.get_session(pod_name)
                if not session:
                    logger.warning("No available session")
                    await asyncio.sleep(0.5)
                    continue
                
                try:
                    profile_data = await self.search_service.search_profile(phone_number)
                    formatted = ProfileAdapter.format_profile(profile_data)
                    
                    await self.queue.set_answer(
                        phone_number,
                        ResponseFormatter.ok(formatted)
                    )
                    
                    await self.session_store.increment_success(
                        session["phone"],
                        session["pod"]
                    )
                    
                    self.count_failures_in_row = 0
                    self.count_reload += 1
                    logger.info("Task completed successfully")
                
                except NoDataError:
                    await self._handle_no_data(phone_number, session)
                
                except AccountLockedException:
                    await self._handle_account_locked(phone_number, session)
                    break
                
                except Exception as e:
                    logger.error(f"Unexpected error: {e}")
                    await self._handle_return_to_queue(phone_number, session)
            
            except Exception as e:
                logger.error(f"Worker loop error: {e}")
                await asyncio.sleep(1)
        
        logger.info("Worker stopped")
    
    async def _handle_no_data(self, phone: str, session: dict):
        await self.queue.set_answer(phone, ResponseFormatter.empty())
        await self.session_store.increment_success(session["phone"], session["pod"])
        logger.info("No data found - task completed")
    
    async def _handle_account_locked(self, phone: str, session: dict):
        await self.queue.set_answer(
            phone,
            ResponseFormatter.error("Account locked", 506)
        )
        await self.session_store.block_session(session["phone"], session["pod"])
        logger.error("Account locked - blocking session")
    
    async def _handle_return_to_queue(self, phone: str, session: dict):
        await self.queue.return_to_queue(phone)
        await self.queue.set_answer(
            phone,
            ResponseFormatter.error("Task returned to queue", 500)
        )
        self.count_failures_in_row += 1
        logger.warning("Returned task to queue")
    
    def _is_alive(self) -> bool:
        if self.count_reload == 0:
            return True
        if self.count_reload >= settings.COUNT_USE_FOR_RELOAD:
            logger.info("Reload limit reached")
            return False
        if self.count_failures_in_row >= settings.MAX_FAILURES_IN_ROW:
            logger.error("Too many failures")
            return False
        return True