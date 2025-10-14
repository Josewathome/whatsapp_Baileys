# ============================================================================
# File: controllers/enhanced_whatsapp_controller.py (FIXED)
# ============================================================================
import logging
import asyncio
from typing import Dict, Optional
from app.domain.services.session_registration_service import SessionRegistrationService
from app.domain.services.connection_manager import ConnectionManager, ConnectionState
from app.infrastructure.health.health_monitor import HealthMonitor
from app.infrastructure.keydb.adapters import ProfileAdapter, ResponseFormatter
from app.core.config import settings

logger = logging.getLogger(__name__)


class EnhancedWhatsAppController:
    """Enhanced controller with session registration and connection management"""
    
    def __init__(
        self,
        search_service,
        session_store,
        queue,
        whatsapp_client,
        pod_name: str
    ):
        self.search_service = search_service
        self.session_store = session_store
        self.queue = queue
        self.whatsapp_client = whatsapp_client
        self.pod_name = pod_name
        
        # Enhanced components
        self.registration_service = SessionRegistrationService(
            whatsapp_client, session_store
        )
        self.connection_manager = ConnectionManager(
            whatsapp_client, session_store
        )
        self.health_monitor = HealthMonitor(
            settings.HEALTH_CHECK_FILE,
            settings.HEALTH_CHECK_PERIOD
        )
        
        self.is_running = False
        self.current_session: Optional[Dict] = None
    
    async def initialize(self) -> bool:
        """Initialize the controller with session and connection"""
        try:
            logger.info("Initializing enhanced WhatsApp controller")
            
            # Get current session
            self.current_session = await self.session_store.get_session(self.pod_name)
            
            if not self.current_session:
                logger.warning("No active session found - registration required")
                return False
            
            # Initialize connection
            connection_ok = await self.connection_manager.initialize_connection(
                phone=self.current_session["phone"],
                pod=self.pod_name
            )
            
            if connection_ok:
                # Start health monitoring
                asyncio.create_task(self.health_monitor.start_health_loop())
                
                # Set up connection event handlers
                self._setup_connection_handlers()
                
                logger.info("Enhanced controller initialized successfully")
                return True
            else:
                logger.error("Failed to initialize connection")
                return False
        
        except Exception as e:
            logger.error(f"Controller initialization failed: {e}")
            return False
    
    async def start_registration(self) -> Dict:
        """Start new session registration"""
        try:
            registration_data = await self.registration_service.start_registration(
                self.pod_name
            )
            
            logger.info(f"Registration started: {registration_data['session_id']}")
            return registration_data
        
        except Exception as e:
            logger.error(f"Registration start failed: {e}")
            raise
    
    async def complete_registration(self, session_id: str, phone_number: str) -> bool:
        """Complete session registration"""
        try:
            success = await self.registration_service.validate_session(
                session_id, phone_number
            )
            
            if success:
                # Reinitialize with new session
                await self.initialize()
                logger.info("Registration completed successfully")
            else:
                logger.error("Registration validation failed")
            
            return success
        
        except Exception as e:
            logger.error(f"Registration completion failed: {e}")
            raise
    
    async def start_worker(self):
        """Start enhanced background worker"""
        if not await self.initialize():
            logger.error("Cannot start worker - initialization failed")
            return
        
        logger.info("Enhanced worker started. Ready for tasks!")
        self.is_running = True
        
        while self._is_alive():
            try:
                # Check health
                if not await self.health_monitor.check_health():
                    logger.error("Health check failed")
                    break
                
                # Check connection state
                if self.connection_manager.get_state() != ConnectionState.CONNECTED:
                    logger.warning("Connection not ready - skipping task processing")
                    await asyncio.sleep(1)
                    continue
                
                # Process queue tasks
                phone_number = await self.queue.check_queue()
                
                if not phone_number:
                    await asyncio.sleep(0.1)
                    continue
                
                await self._process_task(phone_number)
                
            except Exception as e:
                logger.error(f"Worker loop error: {e}")
                await asyncio.sleep(1)
        
        logger.info("Enhanced worker stopped")
        self.is_running = False
    
    async def _process_task(self, phone_number: str):
        """Process a single queue task"""
        try:
            logger.info(f"Processing task: {phone_number}")
            
            # Update health checkpoint
            await self.health_monitor.checkpoint()
            
            # Process the task
            profile_data = await self.search_service.search_profile(phone_number)
            formatted = ProfileAdapter.format_profile(profile_data)
            
            await self.queue.set_answer(
                phone_number,
                ResponseFormatter.ok(formatted)
            )
            
            # Update session success count
            if self.current_session:
                await self.session_store.increment_success(
                    self.current_session["phone"],
                    self.current_session["pod"]
                )
            
            logger.info("Task completed successfully")
            
        except Exception as e:
            logger.error(f"Task processing failed: {e}")
            await self._handle_task_error(phone_number, e)
    
    async def _handle_task_error(self, phone_number: str, error: Exception):
        """Handle task processing errors"""
        from domain.exceptions import NoDataError, AccountLockedException
        
        try:
            if isinstance(error, NoDataError):
                await self.queue.set_answer(phone_number, ResponseFormatter.empty())
                logger.info("No data found - task completed")
            
            elif isinstance(error, AccountLockedException):
                await self.queue.set_answer(
                    phone_number, 
                    ResponseFormatter.error("Account locked", 506)
                )
                if self.current_session:
                    await self.session_store.block_session(
                        self.current_session["phone"],
                        self.current_session["pod"]
                    )
                logger.error("Account locked - blocking session")
            
            else:
                await self.queue.return_to_queue(phone_number)
                await self.queue.set_answer(
                    phone_number,
                    ResponseFormatter.error("Task returned to queue", 500)
                )
                logger.warning("Returned task to queue")
        
        except Exception as e:
            logger.error(f"Error handling failed: {e}")
    
    def _setup_connection_handlers(self):
        """Set up connection event handlers"""
        self.connection_manager.on("connected", self._on_connected)
        self.connection_manager.on("disconnected", self._on_disconnected)
        self.connection_manager.on("logout", self._on_logout)
        self.connection_manager.on("ban", self._on_ban)
        self.connection_manager.on("restart", self._on_restart)
    
    async def _on_connected(self, data: Dict):
        """Handle connection established"""
        logger.info("Connection established - ready for processing")
        await self.health_monitor.checkpoint()
    
    async def _on_disconnected(self, data: Dict):
        """Handle connection lost"""
        logger.warning("Connection lost - pausing processing")
    
    async def _on_logout(self, data: Dict):
        """Handle logout event"""
        logger.error("Session logged out - blocking session")
        if self.current_session:
            await self.session_store.block_session(
                self.current_session["phone"],
                self.current_session["pod"]
            )
    
    async def _on_ban(self, data: Dict):
        """Handle ban event"""
        logger.error("Possible ban detected - locking session")
        if self.current_session:
            await self.session_store.lock_session(
                self.current_session["phone"],
                self.current_session["pod"],
                duration_seconds=24 * 60 * 60  # 24 hours
            )
    
    async def _on_restart(self, data: Dict):
        """Handle restart required"""
        logger.info("Restart required - reinitializing")
        await self.initialize()
    
    def _is_alive(self) -> bool:
        """Check if worker should continue running"""
        return (self.is_running and 
                self.health_monitor.is_healthy() and
                self.connection_manager.get_state() != ConnectionState.ERROR)
    
    def get_status(self) -> Dict:
        """Get current controller status"""
        return {
            "state": self.connection_manager.get_state().value,
            "pod": self.pod_name,
            "session_phone": self.current_session.get("phone") if self.current_session else None,
            "uptime": self.health_monitor.get_uptime(),
            "healthy": self.health_monitor.is_healthy(),
            "pending_sessions": self.registration_service.get_pending_sessions_count()
        }