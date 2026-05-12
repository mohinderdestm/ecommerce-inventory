from app.core.kafka import KafkaConsumedMessage, kafka_manager
from app.core.logging import get_logger
from app.services.event_bus_service import EventBusService
from app.services.notification_service import NotificationService

logger = get_logger()


class KafkaEventHandler:
    @classmethod
    async def handle(cls, message: KafkaConsumedMessage):
        handler = cls._topic_handlers().get(message.topic, cls._handle_unknown_topic)
        await handler(message)

    @classmethod
    def _topic_handlers(cls):
        return {
            kafka_manager.topic("audit.events"): cls._handle_event_stream,
            kafka_manager.topic("inventory.events"): cls._handle_event_stream,
            kafka_manager.topic("notifications.commands"): cls._handle_notification_command,
            kafka_manager.topic("notifications.events"): cls._handle_event_stream,
            kafka_manager.topic("orders.events"): cls._handle_event_stream,
            kafka_manager.topic("products.events"): cls._handle_event_stream,
            kafka_manager.topic("purchase_orders.events"): cls._handle_event_stream,
        }

    @staticmethod
    async def _handle_notification_command(message: KafkaConsumedMessage):
        command_type = message.value.get("command_type")
        if command_type != "notification.create":
            logger.warning(
                "Ignored Kafka command {} on topic {} partition {} offset {}",
                command_type,
                message.topic,
                message.partition,
                message.offset,
            )
            return

        payload = message.value.get("payload") or {}
        await NotificationService.create_system_notification(**payload)

    @staticmethod
    async def _handle_event_stream(message: KafkaConsumedMessage):
        if not message.value.get("event_type"):
            logger.warning(
                "Ignored Kafka message without event_type on topic {} partition {} offset {}",
                message.topic,
                message.partition,
                message.offset,
            )
            return

        await EventBusService.broadcast_consumed_event(message.topic, message.value)

    @staticmethod
    async def _handle_unknown_topic(message: KafkaConsumedMessage):
        logger.warning(
            "No Kafka handler registered for topic {} partition {} offset {}",
            message.topic,
            message.partition,
            message.offset,
        )
