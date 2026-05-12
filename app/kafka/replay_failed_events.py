from kafka import KafkaConsumer
import json

from app.kafka.config import KAFKA_BROKER
from app.kafka.producer import send_event

consumer = KafkaConsumer(
    "dead_letter_events",
     bootstrap_servers=KAFKA_BROKER,
     value_deserializer=lambda m: json.loads(m.decode("utf-8")),
     auto_offset_reset="earliest",
     enable_auto_commit=True,
     group_id="dlq-replay-group"
)

print("🔁 Replay consumer Started..")

def replay():
    for msg in consumer:
        
        dlq_event = msg.value
        
        print("📥 DLQ Event:", dlq_event)
        
        original_event = dlq_event["event"]
        
        print("♻️ Replaying:", original_event)
        
         # push back to main topic
        send_event("order_events", original_event)
        
        
        print("✅ Event replayed")
        
if __name__ == "__main__":
    replay()
