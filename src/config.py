import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "OrganiStation Notification Service"
    
    # Azure Service Bus
    SERVICE_BUS_NAMESPACE: str = os.getenv("SERVICE_BUS_NAMESPACE", "")
    SERVICE_BUS_TOPIC: str = "notifications"
    SUBSCRIPTIONS: list = ["leave-notifications", "hr-announcements", "manager-notifications"]
    
    # Azure Communication Services
    ACS_CONNECTION_STRING: str = os.getenv("ACS_CONNECTION_STRING", "")
    SENDER_EMAIL: str = "donotreply@organistation.com"
    
    # Azure SignalR
    SIGNALR_CONNECTION_STRING: str = os.getenv("SIGNALR_CONNECTION_STRING", "")
    
    # Security
    JWT_SECRET: str = os.getenv("JWT_SECRET", "change-me-in-prod")
    JWT_ALGORITHM: str = "HS256"
    JWT_ISSUER: str = os.getenv("JWT_ISSUER", "organistation-auth")
    JWT_AUDIENCE: str = os.getenv("JWT_AUDIENCE", "organistation-services")

    class Config:
        case_sensitive = True

settings = Settings()
