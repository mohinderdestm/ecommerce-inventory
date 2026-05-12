import asyncio
import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from app.core.config import settings
from app.core.logging import get_logger

try:
    from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
except ImportError:
    AIOKafkaConsumer = None
    AIOKafkaProducer = None

try:
    from aiokafka.admin import AIOKafkaAdminClient, NewPartitions, NewTopic
except ImportError:
    AIOKafkaAdminClient = None
    NewPartitions = None
    NewTopic = None


logger = get_logger()


@dataclass(frozen=True)
class KafkaTopicDefinition:
    key: str
    partitions: int
    replication_factor: int
    consume: bool = True
    description: str = ""


@dataclass(frozen=True)
class KafkaConsumedMessage:
    topic: str
    partition: int
    offset: int
    key: str | None
    value: dict[str, Any]
    timestamp: int | None = None


MessageHandler = Callable[[KafkaConsumedMessage], Awaitable[None]]


class KafkaManager:
    def __init__(self):
        self._producer = None
        self._consumer = None
        self._consumer_task: asyncio.Task | None = None
        self._handler: MessageHandler | None = None
        self._topic_definitions = self._build_topic_definitions()

    @property
    def enabled(self) -> bool:
        return bool(settings.KAFKA_ENABLED)

    @property
    def available(self) -> bool:
        return AIOKafkaProducer is not None and AIOKafkaConsumer is not None

    @property
    def admin_available(self) -> bool:
        return (
            AIOKafkaAdminClient is not None
            and NewTopic is not None
            and NewPartitions is not None
        )

    @property
    def running(self) -> bool:
        return self._producer is not None and self._consumer is not None

    def topic(self, topic_key: str) -> str:
        return f"{settings.KAFKA_TOPIC_PREFIX}.{topic_key}"

    def topic_definitions(self) -> list[KafkaTopicDefinition]:
        return list(self._topic_definitions)

    def subscribed_topics(self) -> list[str]:
        return [
            self.topic(definition.key)
            for definition in self._topic_definitions
            if definition.consume
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

        self._topic_definitions = self._build_topic_definitions()

        try:
            if settings.KAFKA_AUTO_CREATE_TOPICS:
                await self._ensure_topics()

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
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                client_id=f"{settings.KAFKA_CLIENT_ID}-consumer",
                group_id=settings.KAFKA_GROUP_ID,
                auto_offset_reset=settings.KAFKA_AUTO_OFFSET_RESET,
                enable_auto_commit=True,
                value_deserializer=lambda value: json.loads(value.decode("utf-8")),
                key_deserializer=lambda value: (
                    None if value is None else value.decode("utf-8")
                ),
            )
            self._consumer.subscribe(self.subscribed_topics())
            await self._consumer.start()

            self._consumer_task = asyncio.create_task(self._consume_loop())
            logger.info(
                "Kafka integration started on {} with topics {}",
                settings.KAFKA_BOOTSTRAP_SERVERS,
                self.subscribed_topics(),
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
        self,
        topic: str,
        payload: dict[str, Any],
        key: str | None = None,
        partition: int | None = None,
    ):
        if not self.running or self._producer is None:
            return False

        try:
            metadata = await self._producer.send_and_wait(
                topic, payload, key=key, partition=partition
            )
            logger.info(
                "Kafka publish success topic={} partition={} offset={} key={}",
                topic,
                metadata.partition,
                metadata.offset,
                key,
            )
            return True
        except Exception as exc:
            logger.warning("Kafka publish failed for topic {}: {}", topic, exc)
            return False

    async def _consume_loop(self):
        try:
            async for message in self._consumer:
                if self._handler is None:
                    continue

                consumed_message = KafkaConsumedMessage(
                    topic=message.topic,
                    partition=message.partition,
                    offset=message.offset,
                    key=message.key,
                    value=message.value,
                    timestamp=message.timestamp,
                )

                try:
                    await self._handler(consumed_message)
                except Exception as exc:
                    logger.exception("Kafka message handling failed: {}", exc)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.exception("Kafka consumer loop stopped unexpectedly: {}", exc)

    async def _ensure_topics(self):
        if not self.admin_available:
            logger.info("Kafka admin client is unavailable. Skipping topic provisioning.")
            return

        admin_client = AIOKafkaAdminClient(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            client_id=f"{settings.KAFKA_CLIENT_ID}-admin",
        )

        try:
            await admin_client.start()
            existing_topics = set(await admin_client.list_topics())
            topics_to_create = [
                NewTopic(
                    name=self.topic(definition.key),
                    num_partitions=definition.partitions,
                    replication_factor=definition.replication_factor,
                )
                for definition in self._topic_definitions
                if self.topic(definition.key) not in existing_topics
            ]

            if topics_to_create:
                await admin_client.create_topics(new_topics=topics_to_create)
                logger.info(
                    "Kafka topics created: {}",
                    [topic.name for topic in topics_to_create],
                )

            await self._ensure_topic_partitions(admin_client)
        except Exception as exc:
            logger.warning("Kafka topic provisioning skipped: {}", exc)
        finally:
            close = getattr(admin_client, "close", None)
            if close is not None:
                maybe_coro = close()
                if asyncio.iscoroutine(maybe_coro):
                    await maybe_coro

    async def _ensure_topic_partitions(self, admin_client: AIOKafkaAdminClient):
        described_topics = await admin_client.describe_topics(self.subscribed_topics())
        existing_partitions = {
            topic["topic"]: len(topic.get("partitions", [])) for topic in described_topics
        }

        topics_to_expand: dict[str, NewPartitions] = {}
        for definition in self._topic_definitions:
            topic_name = self.topic(definition.key)
            current_partition_count = existing_partitions.get(topic_name)
            if current_partition_count is None:
                continue
            if current_partition_count >= definition.partitions:
                continue

            topics_to_expand[topic_name] = NewPartitions(
                total_count=definition.partitions
            )

        if not topics_to_expand:
            return

        await admin_client.create_partitions(topics_to_expand)
        logger.info(
            "Kafka topic partitions increased: {}",
            {
                topic_name: new_partitions.total_count
                for topic_name, new_partitions in topics_to_expand.items()
            },
        )

    def _build_topic_definitions(self) -> list[KafkaTopicDefinition]:
        return [
            self._topic_definition(
                "audit.events",
                partitions=1,
                description="Immutable audit trail for security and operations.",
            ),
            self._topic_definition(
                "inventory.events",
                partitions=3,
                description="Inventory adjustments and stock movement events.",
            ),
            self._topic_definition(
                "notifications.commands",
                partitions=2,
                description="Commands requesting notification side effects.",
            ),
            self._topic_definition(
                "notifications.events",
                partitions=2,
                description="Notification lifecycle events for observers.",
            ),
            self._topic_definition(
                "orders.events",
                partitions=6,
                description="Sales order lifecycle events.",
            ),
            self._topic_definition(
                "products.events",
                partitions=3,
                description="Product catalog and SKU change events.",
            ),
            self._topic_definition(
                "purchase_orders.events",
                partitions=4,
                description="Purchase order lifecycle events.",
            ),
        ]

    def _topic_definition(
        self,
        topic_key: str,
        *,
        partitions: int | None,
        description: str,
        consume: bool = True,
    ) -> KafkaTopicDefinition:
        resolved_partitions = settings.KAFKA_TOPIC_PARTITIONS.get(
            topic_key,
            partitions
            if partitions is not None
            else settings.KAFKA_DEFAULT_TOPIC_PARTITIONS,
        )
        return KafkaTopicDefinition(
            key=topic_key,
            partitions=max(1, resolved_partitions),
            replication_factor=settings.KAFKA_TOPIC_REPLICATION_FACTORS.get(
                topic_key, settings.KAFKA_DEFAULT_TOPIC_REPLICATION_FACTOR
            ),
            consume=consume,
            description=description,
        )

    def status(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "available": self.available,
            "admin_available": self.admin_available,
            "running": self.running,
            "bootstrap_servers": settings.KAFKA_BOOTSTRAP_SERVERS,
            "client_id": settings.KAFKA_CLIENT_ID,
            "group_id": settings.KAFKA_GROUP_ID,
            "topic_prefix": settings.KAFKA_TOPIC_PREFIX,
            "topic_auto_create_enabled": settings.KAFKA_AUTO_CREATE_TOPICS,
            "subscribed_topics": self.subscribed_topics(),
            "topic_definitions": [
                {
                    "topic_key": definition.key,
                    "topic": self.topic(definition.key),
                    "partitions": definition.partitions,
                    "replication_factor": definition.replication_factor,
                    "consume": definition.consume,
                    "description": definition.description,
                }
                for definition in self._topic_definitions
            ],
            "message_handler": (
                self._handler.__qualname__ if self._handler is not None else None
            ),
        }


kafka_manager = KafkaManager()
