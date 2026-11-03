from constraints import GridGuardrails

if __name__ == "__main__":
    print("--- TESTOVÁNÍ DETERMINISTICKÝCH MEZÍ (GUARDRAILŮ) ---")
    
    # Testy frekvence
    print(GridGuardrails.evaluate_frequency(50.0))  # Mělo by být OK
    print(GridGuardrails.evaluate_frequency(48.2))  # Mělo by být WARNING_EXTREME
    print(GridGuardrails.evaluate_frequency(46.5))  # Mělo by být VIOLATION
    
    # Testy napětí
    print(GridGuardrails.evaluate_voltage(1.0))   # Mělo by být OK
    print(GridGuardrails.evaluate_voltage(1.12))  # Mělo by být WARNING_STATISTICAL
    print(GridGuardrails.evaluate_voltage(0.80))  # Mělo by být VIOLATION