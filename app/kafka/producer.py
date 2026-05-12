from kafka import KafkaProducer
import json
from app.kafka.config import KAFKA_BROKER
from datetime import datetime

def json_serializer(data):
    def default(o):
        if isinstance(o,datetime):
            return o.isoformat()
        return str(o)
    return json.dumps(data,default=default).encode("utf-8")

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=json_serializer
)    

def send_event(topic: str, data:dict):
    try:
        producer.send(topic,data)
        producer.flush()
        print(f"Event send to {topic}")
    except Exception as e:
        print("Kafka send error:",e)