import asyncio
import json
from collections.abc import Awaitable, Callable
from typing import Any
from app.core.config import settings
from app.core.logging import get_logger

try:
    from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
except ImportError:
    AIOKafkaConsumer = None
    AIOKafkaProducer = None


logger = get_logger()


MessageHandler = Callable[[str, dict[str, Any]], Awaitable[None]]


class KafkaManager:
    def __init__(self):
        self._producer = None
        self._consumer = None
        self._consumer_task: asyncio.Task | None = None
        self._handler: MessageHandler | None = None

    @property
    def enabled(self) -> bool:
        return bool(settings.KAFKA_ENABLED)

    @property
    def available(self) -> bool:
        return AIOKafkaProducer is not None and AIOKafkaConsumer is not None

    @property
    def running(self) -> bool:
        return self._producer is not None and self._consumer is not None

    def topic(self, topic_key: str) -> str:
        return f"{settings.KAFKA_TOPIC_PREFIX}.{topic_key}"

    def subscribed_topics(self) -> list[str]:
        return [
            self.topic("audit.events"),
            self.topic("inventory.events"),
            self.topic("notifications.commands"),
            self.topic("notifications.events"),
            self.topic("orders.events"),
            self.topic("products.events"),
            self.topic("purchase_orders.events"),
        ]

    def set_message_handler(self, handler: MessageHandler):
        self._handler = handler

    async def start(self):
        if not self.enabled:
            logger.info("Kafka integration is disabled.")
            return

        if not self.available:
            logger.warning(
                "Kafka integration is enabled but aiokafka is not installed. "
                "Install dependencies from requirements-kafka.txt."
            )
            return

        if self.running:
            return

        try:
            self._producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                client_id=settings.KAFKA_CLIENT_ID,
                value_serializer=lambda value: json.dumps(value).encode("utf-8"),
                key_serializer=lambda value: (
                    None if value is None else str(value).encode("utf-8")
                ),
            )
            await self._producer.start()

            self._consumer = AIOKafkaConsumer(
                *self.subscribed_topics(),
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                client_id=f"{settings.KAFKA_CLIENT_ID}-consumer",
                group_id=settings.KAFKA_GROUP_ID,
                auto_offset_reset=settings.KAFKA_AUTO_OFFSET_RESET,
                enable_auto_commit=True,
                value_deserializer=lambda value: json.loads(value.decode("utf-8")),
            )
            await self._consumer.start()

            self._consumer_task = asyncio.create_task(self._consume_loop())
            logger.info(
                "Kafka integration started on {}", settings.KAFKA_BOOTSTRAP_SERVERS
            )
        except Exception as exc:
            logger.warning(
                "Kafka startup failed on {}: {}",
                settings.KAFKA_BOOTSTRAP_SERVERS,
                exc,
            )
            await self.stop()

    async def stop(self):
        if self._consumer_task:
            self._consumer_task.cancel()
            try:
                await self._consumer_task
            except asyncio.CancelledError:
                pass
            self._consumer_task = None

        if self._consumer is not None:
            await self._consumer.stop()
            self._consumer = None

        if self._producer is not None:
            await self._producer.stop()
            self._producer = None

    async def publish(
        self, topic: str, payload: dict[str, Any], key: str | None = None
    ):
        if not self.running or self._producer is None:
            return False

        try:
            await self._producer.send_and_wait(topic, payload, key=key)
            return True
        except Exception as exc:
            logger.warning("Kafka publish failed for topic {}: {}", topic, exc)
            return False

    async def _consume_loop(self):
        try:
            async for message in self._consumer:
                if self._handler is None:
                    continue
                try:
                    await self._handler(message.topic, message.value)
                except Exception as exc:
                    logger.exception("Kafka message handling failed: {}", exc)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.exception("Kafka consumer loop stopped unexpectedly: {}", exc)

    def status(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "available": self.available,
            "running": self.running,
            "bootstrap_servers": settings.KAFKA_BOOTSTRAP_SERVERS,
            "topic_prefix": settings.KAFKA_TOPIC_PREFIX,
            "subscribed_topics": self.subscribed_topics(),
        }


kafka_manager = KafkaManager()
