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

print("Consumer spuštěn, zpracovávám telemetrii včetně GPS a meteo kontextu...")

for message in consumer:
    data = message.value
    station_id = data.get('station_id', 'UNKNOWN')
    asset_type = data.get('asset_type', 'substation')
    gps = data.get('gps', {})
    voltage = data.get('voltage', 1.0)
    frequency = data.get('frequency', 50.0)
    conductor_temp = data.get('conductor_temp', 45.0)
    ambient_temp = data.get('ambient_temp', 15.0)
    wind_speed = data.get('wind_speed', 3.0)
    
    # Vyhodnocení guardrailů
    freq_check = GridGuardrails.evaluate_frequency(frequency)
    volt_check = GridGuardrails.evaluate_voltage(voltage)
    temp_check = GridGuardrails.evaluate_conductor_temperature(conductor_temp)
    
    print(f"[{station_id} | {asset_type} | GPS: {gps.get('lat')}, {gps.get('lon')}] -> "
          f"Napětí: {voltage} p.u. [{volt_check['status']}] | "
          f"Frekvence: {frequency} Hz [{freq_check['status']}] | "
          f"Teplota vodiče: {conductor_temp}°C (Vítr: {wind_speed} m/s) [{temp_check['status']}]")
    
    # Reakce na kritickou poruchu
    if freq_check['severity'] == 2 or volt_check['severity'] == 2 or temp_check['severity'] == 2:
        print(f"!!! KRITICKÝ STAV DETEKOVÁN NA STANICI {station_id} !!!")