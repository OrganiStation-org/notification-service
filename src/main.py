import asyncio
import logging
from fastapi import FastAPI, Depends, BackgroundTasks
from .config import settings
from .auth import get_current_user, check_role
from .notifications import notifier
from .service_bus import processor

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("notification-service")

app = FastAPI(title=settings.PROJECT_NAME)

@app.on_event("startup")
async def startup_event():
    logger.info("Notification Service is starting up...")
    # Start Service Bus listener in a background task
    asyncio.create_task(processor.start_all())

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/ready")
async def ready():
    return {"status": "ready"}

@app.post("/notifications/send-email")
async def send_email(data: dict, user: dict = Depends(get_current_user)):
    """Direct email sending API for internal services"""
    await notifier.send_email(data["email"], data["title"], data["message"])
    return {"status": "sent"}

@app.post("/notifications/broadcast")
async def broadcast(data: dict, user: dict = Depends(get_current_user)):
    """Broadcast notification to all or target group (HR only)"""
    check_role(user, "HR")
    # Simulation of broadcast logic
    await notifier.push_realtime(None, data["title"], data["message"], group=data.get("department"))
    return {"status": "broadcast_queued"}

@app.post("/notifications/user/{userId}")
async def notify_user(userId: str, data: dict, user: dict = Depends(get_current_user)):
    """Direct push notification to a specific user"""
    await notifier.push_realtime(userId, data["title"], data["message"])
    return {"status": "pushed"}
