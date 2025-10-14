from pydantic_settings import BaseSettings
from typing import Optional
import socket

class Settings(BaseSettings):
    """Application configuration"""
    
    # Application settings
    SERVICE_NAME: str = "tw.tools.whatsapp"
    MODE: str = "dev"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Session settings
    COUNT_USE_FOR_RELOAD: int = 1000
    SESSION_TIMEOUT: int = 600
    MAX_FAILURES_IN_ROW: int = 30
    SECRETE_KEY: str = "IU2rcG-Pj9F33_T3ldZxeMFcub4JsKUSHtzmBXPpQYQ="
    
    # Health check
    HEALTH_CHECK_FILE: str = "/tmp/app_alive.pid"
    HEALTH_CHECK_PERIOD: int = 60
    
    # Validator service
    VALIDATOR_URL: str = "http://validator-service/api/v1/validate"
    BAILEYS_BRIDGE_URL: str = "http://localhost:3000"
    BASE_URL: str = "http://localhost:8000"
    POD_NAME: str = f"whatsapp-pod-{socket.gethostname()}"
    
    class Config:
        env_file = ".env.example"
        case_sensitive = True


settings = Settings()