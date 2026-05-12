# from kafka import KafkaConsumer
# from app.services.notification_service import NotificationService
# import json
# import asyncio
# from app.kafka.config import KAFKA_BROKER

# consumer = KafkaConsumer(
#     "order_events",
#     bootstrap_servers=KAFKA_BROKER,
#     group_id="notification-group",
#     value_deserializer=lambda m: json.loads(m.decode("utf-8"))
# )

# async def consume():
#     print("🔔 Notification consumer started...")

#     for msg in consumer:
#         event = msg.value
#         print("📥 Event:", event)

#         title = event["type"].replace("_", " ").title()
#         message = f"Order {event['order_id']} is {event['status']}"

#         await NotificationService.create({
#             "user_id": event["user_id"],
#             "title": title,
#             "message": message,
#             "type": "order_update"
#         })

#         print("✅ Notification created")


# if __name__ == "__main__":
#     print("📦 Notification consumer started...")
#     asyncio.run(consume())

from kafka import KafkaConsumer
from app.services.notification_service import NotificationService
import json
import asyncio
from app.kafka.config import KAFKA_BROKER

consumer = KafkaConsumer(
    "order_events",
    bootstrap_servers=KAFKA_BROKER,
    group_id="notification-group",
    value_deserializer=lambda m: json.loads(m.decode("utf-8"))
)

async def consume():
    print("🔔 Notification consumer started...")

    for msg in consumer:
        event = msg.value
        print("📥 Event:", event)

        # ================= LOW STOCK =================
        if event["type"] == "low_stock":

            await NotificationService.create({
                "role": "admin",
                "title": event["title"],
                "message": event["message"],
                "type": "low_stock"
            })

            print("✅ Low stock notification created")
            continue

        # ================= ORDER EVENTS =================
        status = event["status"]

        product_text = ", ".join([
            f"{item['product_name']} (x{item['quantity']})"
            for item in event["items"][:2]
        ])

        if len(event["items"]) > 2:
            product_text += "..."

        title = f"Order {status.title()}"
        message = f"{product_text} {status} (Order #{event['order_id']})"

        # USER notification
        await NotificationService.create({
            "user_id": event["user_id"],
            "title": title,
            "message": message,
            "type": f"order_{status}"
        })

        # ADMIN notification
        await NotificationService.create({
            "role": "admin",
            "title": title,
            "message": message,
            "type": f"order_{status}"
        })

        print("✅ Order notification created")


if __name__ == "__main__":
    asyncio.run(consume())