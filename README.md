## Struktura projektu (gip-pilot)

- `app/` - Hlavní aplikační kontejnery a skripty
  - `mock_producer.py` - Generování a odesílání syntetické telemetrie (napětí, výkon, frekvence) do Kafky
  - `consumer.py` - Ingeste a čtení telemetrických dat z Kafka topicu `gip-telemetry`
  - `math_core/` - Matematické jádro pro výpočty a fyzikální stavy sítě *(připravuje se)*
  - `models/` - AI modely a surf-inference vrstvy
- `docker-compose.yml` - Konfigurace infrastruktury (ZooKeeper, Kafka broker, Python runtime)
- ## ⚡ GIP (Grid Intelligent Platform) - Pilot

Pilotní architektura pro real-time ingestu telemetrických dat, deterministickou validaci podle českých a evropských norem a pokročilé řízení energetické soustavy.

---

### 🚀 Dosavadní stav a implementované moduly

- **Datová pipeline a infrastruktura (`app/`)**:
  - Kontejnerizované prostředí spravované pomocí **Docker Compose** (Apache Kafka + ZooKeeper).
  - `mock_producer.py` – Generování syntetických telemetrických dat (napětí, frekvence, teplota vodičů).
  - `consumer.py` – Asynchronní čtení zpráva z Kafka topicu `gip-telemetry` a okamžitá validace v reálném čase.

- **Deterministické bezpečnostní meze – Guardraily (`app/guardrail/constraints.py`)**:
  - **Frekvence**: Kontrola normálního provozního rozsahu ($49{,}0 - 51{,}0\,\text{Hz}$) a krajních mezí ($47{,}5 - 51{,}5\,\text{Hz}$) pro kontinentální evropskou soustavu.
  - **Napětí**: Vyhodnocení statistických ($0{,}90 - 1{,}10\,\text{p.u.}$) a absolutních mezí ($0{,}85 - 1{,}15\,\text{p.u.}$) pro hladiny VN a 110 kV v souladu s **ČSN EN 50160** a **PPDS**.
  - **Tepelné limity vodičů**: Implementace normy **ČSN EN 50341** pro venkovní holé vodiče (provozní teplota $80\,^\circ\text{C}$, krátkodobá poruchová teplota až $300\,^\circ\text{C}$) a katalogové limity pro izolované kabely podle typu izolace (**PVC, XLPE, EPR, PE, guma**).

---

### 📂 Struktura projektu

- `app/`
  - `consumer.py` – Kafka consumer s integrovaným vyhodnocováním guardrailů
  - `mock_producer.py` – Simulátor generování telemetrických dat
  - `guardrail/`
    - `constraints.py` – Definice norem a vyhodnocovací logika (frekvence, napětí, teploty)
    - `test_constraints.py` – Testovací skripty pro ověření mezí
- `docker-compose.yml` – Konfigurace Kafky a výpočetního prostředí
- `README.md` – Dokumentace projektu
- **Geografický a meteorologický kontext (GPS & Meteo)**:
  - Rozšíření telemetrických zpráv o identifikátory stanic (`station_id`), typy aktiv (`asset_type`) a GPS souřadnice rozvoden a OZE.
  - `meteo_producer.py` – Samostatná služba pro pravidelný sběr aktuálních meteorologických dat (teplota vzduchu, rychlost větru, sluneční radiace) z otevřeného **Open-Meteo API**[cite: 3].
  - Podpora pro budoucí výpočet **Dynamic Line Rating (DLR)** – dynamické zatížení vedení v závislosti na reálném chlazení větrem a okolní teplotě.
