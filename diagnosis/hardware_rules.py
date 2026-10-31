
"""Rule-only diagnosis for the three-sensor ESP32 motor."""

def diagnose_esp32(reading, motor_status, rpm_zero_persistent=False):
    temp = float(reading["temperature_c"])
    current = float(reading["current_a"])
    rpm = float(reading["rpm"])
    status = str(motor_status or "").upper()

    # Preliminary limits: calibrate using real motor tests.
    if temp >= 65:
        fault = "Possible Overheating"
        severity = "CRITICAL"
        explanation = "Temperature at or above 65 C."
        action = "Stop and inspect motor temperature safely."

    elif status == "OFF":
        fault = "Motor Idle"
        severity = "NORMAL"
        explanation = "Motor is commanded OFF."
        action = "No action required."

    elif status != "ON":
        fault = "Motor State Unknown"
        severity = "WARNING"
        explanation = "Motor command state was not reported."
        action = "Verify motor control and telemetry."

    elif current >= 1.70 and rpm <= 100:
        fault = "Possible Motor Stall"
        severity = "CRITICAL"
        explanation = "High current with very low RPM."
        action = "Stop motor and inspect for binding."

    elif current >= 1.05 and rpm < 350:
        fault = "Possible Mechanical Overload"
        severity = "WARNING"
        explanation = "Elevated current and reduced RPM."
        action = "Inspect mechanical load and wiring."

    elif temp >= 55:
        fault = "Possible Thermal Stress"
        severity = "WARNING"
        explanation = "Motor temperature elevated."
        action = "Check ventilation and motor temperature."

    elif rpm <= 0:
        if rpm_zero_persistent:
            fault = "Speed Feedback Missing"
            severity = "WARNING"
            explanation = (
                "Zero RPM persisted across consecutive ON readings."
            )
            action = "Stop motor and inspect motor and IR sensor."
        else:
            fault = "RPM Pending Verification"
            severity = "NORMAL"
            explanation = (
                "First ON reading with zero RPM; "
                "rotation has not yet been confirmed."
            )
            action = "Verify motor rotation and sensor pulses."

    else:
        fault = "Normal Operation"
        severity = "NORMAL"
        explanation = (
            "Available sensor readings are within "
            "preliminary operating limits."
        )
        action = "Continue monitoring."

    explanation += " Vibration unavailable; ML not evaluated."

    return {
        "event_id": reading["event_id"],
        "device_id": reading["device_id"],
        "timestamp": reading["timestamp"],
        "rule_fault": fault,
        "rule_severity": severity,
        "ml_fault": None,
        "ml_confidence": 0.0,
        "hybrid_fault": fault,
        "hybrid_severity": severity,
        "explanation": explanation,
        "recommended_action": action,
        "conflict_detected": False,
    }
