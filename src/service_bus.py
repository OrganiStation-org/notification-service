import json
import asyncio
import logging
from azure.servicebus.aio import ServiceBusClient
from azure.identity.aio import DefaultAzureCredential
from .config import settings
from .notifications import notifier

logger = logging.getLogger("notification-service")

class ServiceBusProcessor:
    def __init__(self):
        self.client = None
        self.credential = None

    def initialize_client(self):
        if not settings.SERVICE_BUS_NAMESPACE:
            logger.info("SERVICE_BUS_NAMESPACE is not configured. Service Bus listener is disabled.")
            return

        try:
            if "Endpoint=sb://" in settings.SERVICE_BUS_NAMESPACE:
                self.client = ServiceBusClient.from_connection_string(settings.SERVICE_BUS_NAMESPACE)
                logger.info("Service Bus Client initialized via Connection String.")
            else:
                # If namespace name is provided, use Workload Identity / DefaultAzureCredential
                namespace = settings.SERVICE_BUS_NAMESPACE
                if not namespace.endswith(".servicebus.windows.net") and "." not in namespace:
                    namespace = f"{namespace}.servicebus.windows.net"
                
                self.credential = DefaultAzureCredential()
                self.client = ServiceBusClient(
                    fully_qualified_namespace=namespace,
                    credential=self.credential
                )
                logger.info(f"Service Bus Client initialized via DefaultAzureCredential for namespace: {namespace}")
        except Exception as e:
            logger.error(f"Failed to initialize Service Bus Client: {str(e)}")

    async def process_messages(self, subscription_name: str):
        while True:
            try:
                # Get the receiver for the subscription. self.client must be open.
                receiver = self.client.get_subscription_receiver(
                    topic_name=settings.SERVICE_BUS_TOPIC,
                    subscription_name=subscription_name
                )
                async with receiver:
                    logger.info(f"Started listening to subscription: {subscription_name}...")
                    async for msg in receiver:
                        try:
                            body = json.loads(str(msg))
                            await self.handle_event(body)
                            await receiver.complete_message(msg)
                        except Exception as e:
                            logger.error(f"Error processing message in {subscription_name}: {str(e)}")
            except Exception as e:
                logger.error(f"Service Bus connection error in {subscription_name}: {str(e)}")
                # Wait before retrying to avoid CPU spin or flooding logs
                await asyncio.sleep(10)

    async def handle_event(self, event: dict):
        event_type = event.get("eventType")
        recipient_id = event.get("recipientId")
        recipient_email = event.get("recipientEmail")
        title = event.get("title", "New Notification")
        message = event.get("message", "")

        logger.info(f"Processing event {event_type} for {recipient_id}")

        await notifier.push_realtime(recipient_id, title, message)
        if recipient_email:
            await notifier.send_email(recipient_email, title, message)

    async def start_all(self):
        self.initialize_client()
        if not self.client:
            logger.info("Service Bus listener is disabled (no client initialized).")
            return
            
        try:
            # Open the client context exactly once at the top level
            async with self.client:
                tasks = []
                for sub in settings.SUBSCRIPTIONS:
                    tasks.append(self.process_messages(sub))
                await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Service Bus Client session exception: {str(e)}")
        finally:
            if self.credential:
                await self.credential.close()
                logger.info("Service Bus credentials closed.")

processor = ServiceBusProcessor()
