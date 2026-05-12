from kafka import KafkaConsumer
import json
import asyncio
from app.kafka.config import KAFKA_BROKER
from app.core.database import db
from datetime import datetime


consumer = KafkaConsumer(
    "order_events",
    bootstrap_servers=KAFKA_BROKER,
    group_id="audit-group",
    value_deserializer=lambda m: json.loads(m.decode("utf-8"))
)

async def consume():
    print("🧾 Audit consumer started...")

    for msg in consumer:
        event = msg.value
        print("📥 Event:", event)

        log = {
            "user_id": event.get("user_id"),
            "action": event.get("type"),
            "entity_type": "order",
            "entity_id": event.get("order_id"),
            "timestamp": datetime.utcnow(),
            "value": {
                "status": event.get("status"),
                "items": event.get("items")
            }
        }

        await db["audit_logs"].insert_one(log)
        print("✅ Audit saved")



if __name__ == "__main__":
    print("🧾 Audit consumer started...")
    asyncio.run(consume())