class GridGuardrails:
    """
    Deterministické meze pro frekvenci, napětí a tepelné zatížení vodičů
    v souladu s ČSN EN 50160, PPDS, RfG a ČSN EN 50341.
    """
    
    # --- FREKVENCE ---
    FREQ_NOMINAL = 50.0  # Hz
    FREQ_NORMAL_MIN = 49.0  # Hz
    FREQ_NORMAL_MAX = 51.0  # Hz
    FREQ_EXTREME_MIN = 47.5 # Hz
    FREQ_EXTREME_MAX = 51.5 # Hz

    # --- NAPĚTÍ (v p.u. vůči Uc) ---
    VOLTAGE_ABS_MIN = 0.85  
    VOLTAGE_STAT_MIN = 0.90 
    VOLTAGE_STAT_MAX = 1.10 
    VOLTAGE_ABS_MAX = 1.15  

    # --- TEPELNÉ LIMITY VODIČŮ (°C) ---
    # 1. Venkovní holé vodiče (nadzemní vedení nad 45 kV)
    OVERHEAD_NORMAL_MAX = 80.0    # Běžná maximální provozní teplota (min. doporučená 70 °C)
    OVERHEAD_FAULT_MAX = 300.0    # Krátkodobá teplota při poruše (pro vodiče ACSR s ocelovým jádrem)

    # 2. Izolované kabely dle typu izolace (provozní / krátkodobé přetížení)
    CABLE_THERMAL_LIMITS = {
        "PVC": {"normal": 70.0, "overload": 120.0},
        "PE": {"normal": 70.0, "overload": 120.0}, # odhad / orientační dle standardů
        "XLPE": {"normal": 90.0, "overload": 120.0},
        "EPR": {"normal": 90.0, "overload": 130.0},
        "RUBBER": {"normal": 60.0, "overload": 120.0}
    }

    @classmethod
    def evaluate_frequency(cls, frequency: float) -> dict:
        """Vyhodnotí stav frekvence proti normativním mezím."""
        status = "OK"
        severity = 0
        message = "Frekvence v normálním rozsahu."

        if not (cls.FREQ_NORMAL_MIN <= frequency <= cls.FREQ_NORMAL_MAX):
            if cls.FREQ_EXTREME_MIN <= frequency <= cls.FREQ_EXTREME_MAX:
                status = "WARNING_EXTREME"
                severity = 1
                message = f"Frekvence ({frequency} Hz) je v krajním mezném pásmu."
            else:
                status = "VIOLATION"
                severity = 2
                message = f"Kritická porucha frekvence: {frequency} Hz mimo povolené meze!"

        return {"parameter": "frequency", "value": frequency, "status": status, "severity": severity, "message": message}

    @classmethod
    def evaluate_voltage(cls, voltage_pu: float) -> dict:
        """Vyhodnotí stav napětí proti PPDS/EN 50160."""
        status = "OK"
        severity = 0
        message = "Napětí v normálním statistickém rozsahu."

        if not (cls.VOLTAGE_STAT_MIN <= voltage_pu <= cls.VOLTAGE_STAT_MAX):
            if cls.VOLTAGE_ABS_MIN <= voltage_pu <= cls.VOLTAGE_ABS_MAX:
                status = "WARNING_STATISTICAL"
                severity = 1
                message = f"Napětí ({voltage_pu} p.u.) spadá do absolutní (tolerované) meze."
            else:
                status = "VIOLATION"
                severity = 2
                message = f"Kritické překročení mezí napětí: {voltage_pu} p.u.!"

        return {"parameter": "voltage", "value": voltage_pu, "status": status, "severity": severity, "message": message}

    @classmethod
    def evaluate_conductor_temperature(cls, temp_celsius: float, conductor_type: str = "overhead", insulation: str = "XLPE") -> dict:
        """
        Vyhodnotí oteplení/teplotu vodiče (venkovní holé vs. izolovaný kabel).
        conductor_type: 'overhead' (nadzemní) nebo 'cable' (kabelové vedení)
        insulation: typ izolace pro kabely ('PVC', 'XLPE', 'EPR', 'RUBBER', 'PE')
        """
        status = "OK"
        severity = 0
        message = "Teplota vodiče v normálním provozním rozsahu."

        if conductor_type == "overhead":
            if temp_celsius > cls.OVERHEAD_NORMAL_MAX:
                if temp_celsius <= cls.OVERHEAD_FAULT_MAX:
                    status = "WARNING_FAULT_OR_OVERLOAD"
                    severity = 1
                    message = f"Teplota venkovního vodiče ({temp_celsius} °C) překračuje 80 °C (přípustné při poruše/extrémním zatížení až do {cls.OVERHEAD_FAULT_MAX} °C)."
                else:
                    status = "VIOLATION"
                    severity = 2
                    message = f"Kritické přehřátí venkovního vodiče: {temp_celsius} °C překračuje maximální mez!"
        elif conductor_type == "cable":
            limits = cls.CABLE_THERMAL_LIMITS.get(insulation.upper(), {"normal": 90.0, "overload": 120.0})
            normal_limit = limits["normal"]
            overload_limit = limits["overload"]

            if temp_celsius > normal_limit:
                if temp_celsius <= overload_limit:
                    status = "WARNING_OVERLOAD"
                    severity = 1
                    message = f"Teplota kabelu ({temp_celsius} °C, izolace {insulation}) překračuje běžný limit {normal_limit} °C, jedná se o stav přetížení."
                else:
                    status = "VIOLATION"
                    severity = 2
                    message = f"Kritické překročení teploty kabelu s izolací {insulation}: {temp_celsius} °C (limit přetížení je {overload_limit} °C)!"

        return {
            "parameter": "conductor_temperature",
            "value": temp_celsius,
            "conductor_type": conductor_type,
            "insulation": insulation if conductor_type == "cable" else None,
            "status": status,
            "severity": severity,
            "message": message
        }