from app.core.kafka import kafka_manager
from app.core.logging import get_logger
from app.services.event_bus_service import EventBusService
from app.services.notification_service import NotificationService

logger = get_logger()


class KafkaEventHandler:
    @staticmethod
    async def handle(topic: str, message: dict):
        if topic == kafka_manager.topic("notifications.commands"):
            payload = message.get("payload") or {}
            await NotificationService.create_system_notification(**payload)
            return

        if not message.get("event_type"):
            logger.warning(
                "Ignored Kafka message without event_type on topic {}", topic
            )
            return

        await EventBusService.broadcast_consumed_event(topic, message)
