import json
import time
import random
from kafka import KafkaProducer

producer = KafkaProducer(
    bootstrap_servers=['kafka:29092'],
    value_serializer=lambda x: json.dumps(x).encode('utf-8')
)

print("Mock producer spuštěn, odesílám telemetrii s GPS a meteo kontextem...")

# Definice sledovaných rozvoden a zdrojů s GPS
STATIONS = [
    {"station_id": "SUB_KOLIN_110kV", "asset_type": "substation", "lat": 50.0283, "lon": 15.2005},
    {"station_id": "SUB_PRAHA_JINONICE", "asset_type": "substation", "lat": 50.0515, "lon": 14.3653},
    {"station_id": "OZE_FVE_KOLIN", "asset_type": "pv_plant", "lat": 50.0350, "lon": 15.2100}
]

while True:
    for station in STATIONS:
        data = {
            "station_id": station["station_id"],
            "asset_type": station["asset_type"],
            "gps": {
                "lat": station["lat"],
                "lon": station["lon"]
            },
            "voltage": round(random.uniform(0.92, 1.08), 3),       # p.u.
            "frequency": round(random.uniform(49.8, 50.2), 2),     # Hz
            "conductor_temp": round(random.uniform(35.0, 85.0), 1),# °C
            "ambient_temp": round(random.uniform(5.0, 30.0), 1),   # °C
            "wind_speed": round(random.uniform(0.5, 12.0), 1)      # m/s
        }
        
        producer.send('gip-telemetry', value=data)
        print(f"Odesláno -> {data['station_id']} | GPS: {data['gps']} | Napětí: {data['voltage']} p.u. | Teplota: {data['conductor_temp']} °C")
        
    time.sleep(5)