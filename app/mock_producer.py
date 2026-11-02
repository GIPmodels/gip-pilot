import json
import random
import time
from kafka import KafkaProducer

producer = KafkaProducer(
    bootstrap_servers=['kafka:29092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

TOPIC_NAME = 'gip-telemetry'

print(f"Spouštím mock producenta. Odesílám data do topicu '{TOPIC_NAME}'...")

try:
    while True:
        telemetry_data = {
            "timestamp": time.time(),
            "node_id": "node_substation_01",
            "voltage_kv": round(random.uniform(395.0, 405.0), 2),
            "active_power_mw": round(random.uniform(45.0, 55.0), 2),
            "frequency_hz": round(random.uniform(49.95, 50.05), 3)
        }
        producer.send(TOPIC_NAME, value=telemetry_data)
        print(f"Odesláno: {telemetry_data}")
        time.sleep(1.0)
except KeyboardInterrupt:
    print("Producent byl zastaven.")
finally:
    producer.close()