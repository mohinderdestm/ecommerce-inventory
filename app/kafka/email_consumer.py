from kafka import KafkaConsumer
import json
import asyncio
from datetime import datetime

from app.kafka.config import KAFKA_BROKER
from app.kafka.producer import send_event
from app.services.email_service import send_email_with_pdf
from app.services.email_event_service import EmailEventService

consumer = KafkaConsumer(
    "order_events",
    bootstrap_servers=KAFKA_BROKER,
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    auto_offset_reset="earliest",
    enable_auto_commit=True,
    group_id="email-group"
)

print("📧 Email consumer started...")


async def consume():

    for msg in consumer:

        event = msg.value

        print("📥 Event:", event)

        # ================= ONLY ORDER EVENTS =================
        if not event["type"].startswith("ORDER_"):
            continue

        # ================= EMAIL REQUIRED =================
        if not event.get("email"):
            continue

        try:

            # ================= PROCESSING STATUS =================
            await EmailEventService.update(
                event["event_id"],
                {
                    "status": "PROCESSING"
                }
            )

            subject = f"Order {event['status'].title()}"

            product_text = ", ".join([
                f"{item['product_name']} (x{item['quantity']})"
                for item in event["items"]
            ])

            html = f"""
            <h2>{subject}</h2>

            <p>Hello {event['customer']},</p>

            <p>
                Your order status is now:
                <b>{event['status']}</b>
            </p>

            <p>
                Products:
                {product_text}
            </p>

            <p>
                Order ID:
                {event['order_id']}
            </p>

            <p>
                Total:
                ₹{event['total']}
            </p>
            """

            # ================= SEND EMAIL =================
            await send_email_with_pdf(
                event["email"],
                subject,
                html
            )

            # ================= SUCCESS STATUS =================
            await EmailEventService.update(
                event["event_id"],
                {
                    "status": "SUCCESS"
                }
            )

            print("Order email sent")

        except Exception as e:

            print("Email failed:", e)

            retry_count = event.get("retry_count", 0) + 1

            # ================= FAILED STATUS =================
            await EmailEventService.update(
                event["event_id"],
                {
                    "status": "FAILED",
                    "retry_count": retry_count,
                    "error": str(e)
                }
            )

            # ================= RETRY BACKOFF =================
            delay_map = [5, 30, 60 ]

            if retry_count <= 3:

                delay = delay_map[retry_count - 1]

                print(f"⏳ Retrying in {delay} sec...")

                await asyncio.sleep(delay)

                event["retry_count"] = retry_count

                send_event("order_events", event)

            else:

                print("Max retries exceeded")
                print("Event moved to failed state")
                
                send_event("dead_letter_events", {
                   "event": event,
                   "reason": str(e),
                   "failed_at": datetime.utcnow().isoformat()
                 })
                
               
if __name__ == "__main__":
    asyncio.run(consume())


