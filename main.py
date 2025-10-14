import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Path
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.controllers.whatsapp_controller import WhatsAppController
from app.domain.services.search_service import SearchService
from app.domain.services.exists_service import ExistsService
from app.domain.services.status_service import StatusService
from app.domain.services.business_service import BusinessService
from app.domain.services.avatar_service import AvatarService
from app.infrastructure.baileys.whatsapp_client import WhatsAppClient
from app.infrastructure.session.memory_store import InMemorySessionStore
from app.infrastructure.keydb.queue import InMemoryQueue
from app.infrastructure.logging.logger import setup_logging
from app.core.config import settings
from app.controllers.enhanced_whatsapp_controller import EnhancedWhatsAppController
from app.api.routes import router as api_router
from app.api.session_routes import router as session_router
import os
from fastapi.responses import JSONResponse
import urllib.parse
from app.infrastructure.qrcode import display_qr_from_api

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Enhanced application lifespan management"""
    logger.info(f"Starting {settings.SERVICE_NAME}")
    
    # Initialize components
    whatsapp_client = WhatsAppClient(settings.BAILEYS_BRIDGE_URL)
    
    # Initialize domain services
    exists_service = ExistsService(whatsapp_client)
    status_service = StatusService(whatsapp_client)
    business_service = BusinessService(whatsapp_client)
    avatar_service = AvatarService(whatsapp_client)
    
    search_service = SearchService(
        exists_service,
        status_service,
        business_service,
        avatar_service
    )
    
    # Initialize infrastructure
    session_store = InMemorySessionStore()
    queue = InMemoryQueue("whatsapp_queue")
    
    # Get pod name (from environment or hostname)
    pod_name = os.getenv("POD_NAME", "default-pod")
    
    # Initialize enhanced controller
    enhanced_controller = EnhancedWhatsAppController(
        search_service=search_service,
        session_store=session_store,
        queue=queue,
        whatsapp_client=whatsapp_client,
        pod_name=pod_name
    )
    
    # Store in app state
    app.state.enhanced_controller = enhanced_controller
    app.state.session_store = session_store
    app.state.queue = queue
    
    # Start background worker
    asyncio.create_task(enhanced_controller.start_worker())
    
    logger.info("Enhanced application started successfully")
    
    yield
    
    # Cleanup
    enhanced_controller.is_running = False
    logger.info("Application shutdown complete")


app = FastAPI(
    title="WhatsApp Profile Lookup Service - Enhanced",
    description="Enhanced service with session registration and connection management",
    version="2.0.0",
    lifespan=lifespan
)

# Add middleware and routers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")
app.include_router(session_router, prefix="/api/v1")
app.include_router(router, prefix="/api/v1", tags=["whatsapp"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": settings.SERVICE_NAME,
        "version": "1.0.0",
        "status": "running"
    }
from fastapi import Request

@app.get("/api/v1/qrcode")
async def show_qr(request: Request):
    """
    Example:
    http://localhost:8000/api/v1/qrcode?data=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0i...
    """
    data = request.query_params.get("data")
    if not data:
        return JSONResponse({"error": "Missing 'data' query parameter"}, status_code=400)

    decoded_data = urllib.parse.unquote(data)
    print(f"The decoded data being passed: {decoded_data}")

    try:
        display_qr_from_api(decoded_data)
        return JSONResponse({"status": "QR code displayed in browser"})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.MODE == "dev",
        log_level="info"
    )