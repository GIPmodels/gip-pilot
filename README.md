## Struktura projektu (gip-pilot)

- `app/` - Hlavní aplikační kontejnery a skripty
  - `mock_producer.py` - Generování a odesílání syntetické telemetrie (napětí, výkon, frekvence) do Kafky
  - `consumer.py` - Ingeste a čtení telemetrických dat z Kafka topicu `gip-telemetry`
  - `math_core/` - Matematické jádro pro výpočty a fyzikální stavy sítě *(připravuje se)*
  - `models/` - AI modely a surf-inference vrstvy
- `docker-compose.yml` - Konfigurace infrastruktury (ZooKeeper, Kafka broker, Python runtime)
