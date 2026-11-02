import json
from kafka import KafkaConsumer

consumer = KafkaConsumer(
    'gip-telemetry',
    bootstrap_servers=['kafka:29092'],
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='gip-telemetry-group',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

print("Spouštím Kafka consumera. Čekám na data...")

try:
    for message in consumer:
        data = message.value
        print(f"Přečteno z partition {message.partition} [offset {message.offset}]: {data}")
except KeyboardInterrupt:
    print("Consumer byl zastaven.")
finally:
    consumer.close()