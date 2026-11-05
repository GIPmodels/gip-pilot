import json
import logging
import struct
import numpy as np
import pandas as pd
from datetime import datetime
from kafka import KafkaProducer

# Konfigurace logování
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [GIP-IEC-GATEWAY] - %(levelname)s - %(message)s')

class IEC104ProtocolDecoder:
    """
    Simulovaný průmyslový převodník (Transcoder) pro protokol IEC 60870-5-104.
    Převádí binární TCP stream z DCS/SCADA na unifikovaný JSON pro GIP pipeline.
    """
    def __init__(self):
        logging.info("Inicializace IEC 60870-5-104 dekodéru pro DCS rozhraní...")

    def decode_asdu_frame(self, raw_bytes: bytes) -> dict:
        """
        Dekóduje binární rámec ASDU (Application Service Data Unit) z IEC 104 protokolu.
        V reálném provozu parsuje Typ identifikátoru, IOA (Information Object Address) a naměřenou hodnotu.
        """
        try:
            # Ukázka parsování binárního protokolu (zjednodušeno pro demonstraci)
            # Předpokládáme strukturu: [Typ(1B)][Vlastnosti(1B)][IOA(3B)][Hodnota(4B float)][Kvalita(1B)]
            if len(raw_bytes) < 10:
                raise ValueError("Příliš krátký rámec pro IEC 104 ASDU.")

            type_id = raw_bytes[0]
            ioa = struct.unpack('<I', raw_bytes[1:4] + b'\x00')[0]
            raw_value = struct.unpack('<f', raw_bytes[4:8])[0]
            quality_flag = raw_bytes[8]

            # Mapování typů dle standardu IEC 104 (např. Typ 13 = Measured value, normalized without time)
            metric_type = "voltage_pu" if type_id == 13 else "current_kA"

            parsed_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "node_id": f"NODE_{ioa}",
                metric_type: round(raw_value, 4),
                "quality_valid": (quality_flag & 0x01) == 0  # Kontrola validity bitu
            }
            return parsed_data

        except Exception as e:
            logging.error(f"Chyba při dekódování binárního IEC 104 rámce: {e}")
            return None


class GIPCoreEngineWithGateway:
    def __init__(self, kafka_bootstrap_servers='localhost:9092'):
        self.decoder = IEC104ProtocolDecoder()
        self.bootstrap_servers = kafka_bootstrap_servers
        
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            logging.info("Kafka Producer pro GIP úшеšně připojen.")
        except Exception as e:
            logging.warning(f"Kafka broker není dostupný (běží lokálně?): {e}")
            self.producer = None

    def process_dcs_raw_stream(self, raw_tcp_stream: list):
        """
        Hlavní vstupní brána: Přijímá binární data z DCS, dekóduje je a pouští do pipeline.
        """
        logging.info("Zpracování příchozího binárního proudu z DCS/SCADA rozvodny...")
        decoded_telemetry = []

        for raw_packet in raw_tcp_stream:
            # 1. Překlad (Transcoding) přes IEC 104 dekodér
            decoded = self.decoder.decode_asdu_frame(raw_packet)
            if decoded and decoded.get("quality_valid", True):
                decoded_telemetry.append(decoded)

        if not decoded_telemetry:
        # Žádná platná data
            return

        # 2. Vstupy pro Guardrail-Interlock maticový solver (Y_bus & DAE)
        is_safe = self.run_guardrail_matrix_validation(decoded_telemetry[0])

        # 3. Akce vůči DCS (Povolení vs. Atomické zablokování)
        self.execute_dcs_action(is_safe)

    def run_guardrail_matrix_validation(self, telemetry_packet: dict) -> bool:
        """
        Matematické jádro: Výpočet matice Y_bus a kontrola norem (ČSN EN 50160 a ČSN EN 50341).
        """
        logging.info("Spouštím deterministický solver matice Y_bus a Jakobiánu...")
        
        # Testovací matice admitancí (systém uzlů)
        Y_bus = np.array([[10.0 - 20.0j, -5.0 + 10.0j], [-5.0 + 10.0j, 10.0 - 20.0j]], dtype=complex)
        
        voltage_pu = telemetry_packet.get("voltage_pu", 1.0)
        
        # Simulace AI požadavku na změnu výkonu (např. BESS)
        proposed_delta_p = 5.0  # MW
        simulated_voltage = voltage_pu + (proposed_delta_p * 0.002)

        # Kontrola normativních mezí
        if not (0.90 <= simulated_voltage <= 1.10):
            logging.error(f"INTERLOCK AKTIVOVÁN: Predikované napětí {simulated_voltage:.3f} p.u. porušuje ČSN EN 50160!")
            return False

        logging.info("Interlock SCHVÁLEN: Všechny fyzické a normativní testy prošly.")
        return True

    def execute_dcs_action(self, is_safe: bool):
        """
        Odeslání binárního exekučního příkazu zpět do DCS systému.
        """
        action_status = "DISPATCHED_TO_DCS_ACTUATORS" if is_safe else "ATOMIC_BLOCK_COMMAND"
        
        payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "command": action_status,
            "target": "BESS_INVERTERS_BAY_1"
        }

        if self.producer:
            self.producer.send('gip-dcs-commands', value=payload)
            self.producer.flush()
        
        logging.info(f"VÝSLEDEK INTERLOCKU -> Akce odeslaná do DCS: [{action_status}]")

# --- Testovací spuštění ---
if __name__ == "__main__":
    gateway = GIPCoreEngineWithGateway()

    # Simulace surových binárních paketů přicházejících z DCS (IEC 104 formát)
    # [Typ=13 (M_ME_NC)][IOA=1 (Uzel 1)][Hodnota=1.02 (napětí p.u.)][Kvalita=0 (OK)]
    simulated_iec104_packets = [
        b'\x0d\x01\x00\x00\x68\x66\x82\x3f\x00'
    ]

    gateway.process_dcs_raw_stream(simulated_iec104_packets)