import json
from kafka import KafkaConsumer
from guardrail.constraints import GridGuardrails

consumer = KafkaConsumer(
    'gip-telemetry',
    bootstrap_servers=['kafka:29092'],
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='gip-consumer-group',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

print("Consumer spuštěn, čekám na telemetrická data a ověřuji guardraily...")

for message in consumer:
    data = message.value
    voltage = data.get('voltage', 1.0)
    frequency = data.get('frequency', 50.0)
    
    # Vyhodnocení guardrailů
    freq_check = GridGuardrails.evaluate_frequency(frequency)
    volt_check = GridGuardrails.evaluate_voltage(voltage)
    
    print(f"Přijato -> Napětí: {voltage} p.u. [{volt_check['status']}] | Frekvence: {frequency} Hz [{freq_check['status']}]")
    
    # Reakce na kritickou poruchu
    if freq_check['severity'] == 2 or volt_check['severity'] == 2:
        print(f"!!! KRITICKÝ STAV DETEKOVÁN !!!")