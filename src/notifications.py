import logging
from azure.communication.email import EmailClient
try:
    from azure.messaging.webpubsubservice import WebPubSubServiceClient 
except ImportError:
    WebPubSubServiceClient = None
    
from .config import settings

logger = logging.getLogger("notification-service")

class NotificationManager:
    def __init__(self):
        self.email_client = None
        if settings.ACS_CONNECTION_STRING:
            try:
                self.email_client = EmailClient.from_connection_string(settings.ACS_CONNECTION_STRING)
                logger.info("Azure Email Client initialized.")
            except Exception as e:
                logger.error(f"Failed to init Email Client: {e}")
        
        self.webpubsub_client = None
        if settings.SIGNALR_CONNECTION_STRING and WebPubSubServiceClient:
            try:
                # We use WebPubSub for real-time notifications
                self.webpubsub_client = WebPubSubServiceClient.from_connection_string(
                    settings.SIGNALR_CONNECTION_STRING, 
                    hub="notifications"
                )
                logger.info("Azure WebPubSub Client initialized.")
            except Exception as e:
                logger.error(f"Failed to init WebPubSub: {e}")

    async def send_email(self, recipient: str, title: str, content: str):
        if not self.email_client:
            logger.warning(f"Email client not configured. Skip sending to {recipient}")
            return
        
        try:
            message = {
                "content": {
                    "subject": title,
                    "plainText": content,
                },
                "recipients": {
                    "to": [{"address": recipient}]
                },
                "senderAddress": settings.SENDER_EMAIL
            }
            poller = self.email_client.begin_send(message)
            logger.info(f"Email queued for {recipient}: {title}")
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")

    async def push_realtime(self, user_id: str, title: str, message: str, group: str = None):
        if not self.webpubsub_client:
            logger.warning(f"WebPubSub not configured. Real-time push skipped for {user_id or group}")
            return

        try:
            payload = {"title": title, "message": message, "userId": user_id}
            if group:
                self.webpubsub_client.send_to_group(group, message=payload)
            else:
                # In a real app we'd map user_id to a connection, here we broadcast or use filter
                self.webpubsub_client.send_to_all(message=payload)
            logger.info(f"Real-time push sent to {user_id or group}: {title}")
        except Exception as e:
            logger.error(f"Failed to push real-time notification: {e}")

notifier = NotificationManager()
