from app.kafka.producer import send_event
from datetime import datetime
import uuid
import time

TOTAL_EVENTS = 1000

for i in range(TOTAL_EVENTS):

    event = {
        "event_id": str(uuid.uuid4()),
        "type": "ORDER_CONFIRMED",
        "order_id": f"ORDER-{i}",
        "user_id": "test-user",
        "email": "gagank1019@gmail.com",
        "status": "confirmed",
        "customer": "Load Test User",
        "total": 999,

        "items": [
            {
                "product_id": "P100",
                "product_name": "iPhone",
                "quantity": 1,
                "price": 999
            }
        ],

        "timestamp": datetime.utcnow().isoformat()
    }

    send_event("order_events", event)

    print(f"Sent event {i+1}")

print("DONE")