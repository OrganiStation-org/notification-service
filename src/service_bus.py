import json
import asyncio
import logging
from azure.servicebus.aio import ServiceBusClient
from .config import settings
from .notifications import notifier

logger = logging.getLogger("notification-service")

class ServiceBusProcessor:
    def __init__(self):
        self.client = ServiceBusClient.from_connection_string(settings.SERVICE_BUS_NAMESPACE) if settings.SERVICE_BUS_NAMESPACE else None

    async def process_messages(self, subscription_name: str):
        if not self.client:
            logger.warning(f"Service Bus not configured for {subscription_name}")
            return

        async with self.client:
            receiver = self.client.get_subscription_receiver(
                topic_name=settings.SERVICE_BUS_TOPIC,
                subscription_name=subscription_name
            )
            async with receiver:
                logger.info(f"Started listening to {subscription_name}...")
                async for msg in receiver:
                    try:
                        body = json.loads(str(msg))
                        await self.handle_event(body)
                        await receiver.complete_message(msg)
                    except Exception as e:
                        logger.error(f"Error processing message in {subscription_name}: {str(e)}")
                        # Msg will stay in queue if not completed

    async def handle_event(self, event: dict):
        event_type = event.get("eventType")
        recipient_id = event.get("recipientId")
        recipient_email = event.get("recipientEmail")
        title = event.get("title", "New Notification")
        message = event.get("message", "")

        logger.info(f"Processing event {event_type} for {recipient_id}")

        # 1. Real-time push (Transient)
        await notifier.push_realtime(recipient_id, title, message)

        # 2. Email Notification
        if recipient_email:
            await notifier.send_email(recipient_email, title, message)

    async def start_all(self):
        tasks = []
        for sub in settings.SUBSCRIPTIONS:
            tasks.append(self.process_messages(sub))
        await asyncio.gather(*tasks)

processor = ServiceBusProcessor()
