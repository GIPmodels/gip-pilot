import json
import time
import requests
from kafka import KafkaProducer

# Konfigurace Kafka producenta pro meteo data
producer = KafkaProducer(
    bootstrap_servers=['kafka:29092'],
    value_serializer=lambda x: json.dumps(x).encode('utf-8')
)

# Seznam sledovaných rozvoden s GPS souřadnicemi
LOCATIONS = [
    {"station_id": "SUB_KOLIN_110kV", "lat": 50.0283, "lon": 15.2005},
    {"station_id": "SUB_PRAHA_JINONICE", "lat": 50.0515, "lon": 14.3653}
]

def fetch_weather(lat: float, lon: float) -> dict:
    """Stáhne aktuální data z Open-Meteo API."""
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,wind_speed_10m,direct_radiation"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json().get("current", {})
    except Exception as e:
        print(f"Chyba při stahování meteo dat: {e}")
    return {}

if __name__ == "__main__":
    print("Meteo producer spuštěn, stahuji meteorologická data...")
    while True:
        for loc in LOCATIONS:
            weather_data = fetch_weather(loc["lat"], loc["lon"])
            payload = {
                "station_id": loc["station_id"],
                "gps": {"lat": loc["lat"], "lon": loc["lon"]},
                "timestamp": time.time(),
                "weather": weather_data  # obsahuje např. temperature_2m, wind_speed_10m, direct_radiation
            }
            
            producer.send('gip-weather-forecast', value=payload)
            print(f"Odeslána meteo data pro {loc['station_id']}: {weather_data}")
            
        # Opakovat každou hodinu (3600 sekund)
        time.sleep(3600)