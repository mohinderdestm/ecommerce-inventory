from kafka import KafkaConsumer
import json
import asyncio
from app.kafka.config import KAFKA_BROKER
from app.core.database import db

consumer = KafkaConsumer(
    "order_events",
    bootstrap_servers=KAFKA_BROKER,
    group_id="inventory-group",
    value_deserializer=lambda m: json.loads(m.decode("utf-8"))
)


async def consume():
    print("📦 Inventory consumer started...")

    for msg in consumer:
        event = msg.value
        print("📥 Event:", event)

        if event["type"] == "ORDER_CONFIRMED":

            for item in event["items"]:
                await db["inventory"].update_one(
                    {"product_id": item["product_id"]},
                    {"$inc": {"stock": -item["quantity"]}}
                )

            print("✅ Stock deducted")

if __name__ == "__main__":
    print("📦 Inventory consumer started...")
    asyncio.run(consume())