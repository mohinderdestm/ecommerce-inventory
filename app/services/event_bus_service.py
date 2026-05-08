from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from app.core.config import settings
from app.core.json_utils import to_jsonable
from app.core.kafka import kafka_manager
from app.core.websocket_manager import manager


class EventBusService:
    LEGACY_WEBSOCKET_EVENTS = {
        "product.created": "PRODUCT_CREATED",
        "product.updated": "PRODUCT_UPDATED",
        "product.deleted": "PRODUCT_DELETED",
    }

    @staticmethod
    def _actor(user: Optional[dict]):
        if not user:
            return {"id": None, "name": "System", "email": None, "role": "system"}
        return {
            "id": user.get("id"),
            "name": user.get("name"),
            "email": user.get("email"),
            "role": user.get("role"),
        }

    @classmethod
    def _websocket_event_name(cls, event_type: str):
        return cls.LEGACY_WEBSOCKET_EVENTS.get(
            event_type, event_type.upper().replace(".", "_")
        )

    @classmethod
    def _websocket_message(cls, topic: str, envelope: dict[str, Any]):
        return {
            "event": cls._websocket_event_name(envelope.get("event_type", topic)),
            "topic": topic,
            "data": envelope,
        }

    @classmethod
    async def publish(
        cls,
        *,
        topic_key: str,
        event_type: str,
        aggregate_type: str,
        aggregate_id: str | None = None,
        payload: Any = None,
        metadata: dict[str, Any] | None = None,
        user: dict | None = None,
    ):
        topic = kafka_manager.topic(topic_key)
        envelope = {
            "event_id": uuid4().hex,
            "event_type": event_type,
            "aggregate_type": aggregate_type,
            "aggregate_id": str(aggregate_id) if aggregate_id is not None else None,
            "occurred_at": datetime.utcnow().isoformat(),
            "source": settings.APP_NAME,
            "actor": cls._actor(user),
            "payload": to_jsonable(payload or {}),
            "metadata": to_jsonable(metadata or {}),
        }

        published = await kafka_manager.publish(
            topic, envelope, key=str(aggregate_id) if aggregate_id is not None else None
        )
        if not published:
            await manager.broadcast(cls._websocket_message(topic, envelope))

        return envelope

    @classmethod
    async def broadcast_consumed_event(cls, topic: str, envelope: dict[str, Any]):
        await manager.broadcast(cls._websocket_message(topic, envelope))
