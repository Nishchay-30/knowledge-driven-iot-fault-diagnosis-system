"""
Prescriptive Maintenance Recommendations Module.
Provides structured diagnostic actions, root cause hypotheses, and maintenance procedures
for detected fault conditions.
"""

from typing import Dict, Any, List

FAULT_RECOMMENDATIONS: Dict[str, Dict[str, Any]] = {
    "Normal": {
        "severity": "NORMAL",
        "short_action": "No immediate intervention required. Maintain routine preventive inspections.",
        "root_causes": ["System operating within designed nominal operational envelope."],
        "checklist": [
            "Log operational telemetry hours for routine service scheduling.",
            "Verify lubrication levels every 500 operating hours.",
            "Inspect physical chassis for dust accumulation."
        ],
        "urgency": "Routine",
        "estimated_downtime_minutes": 0,
    },
    "Mechanical Overload": {
        "severity": "WARNING",
        "short_action": "Reduce conveyor/load torque demand; inspect mechanical drivetrain for binding or foreign body jamming.",
        "root_causes": [
            "Excess mechanical load exceeding 12V DC motor rated torque capacity.",
            "Bearing dry friction or gearbox misalignment causing mechanical binding.",
            "Foreign object debris obstructing mechanical output shaft."
        ],
        "checklist": [
            "De-energize drive and rotate shaft manually to feel for binding or resistance.",
            "Measure DC bus current with an external clamp meter to verify ACS712 accuracy.",
            "Check conveyor belt tension and gearbox lubrication.",
            "Verify motor rated continuous current (0.80 A) is not continuously exceeded."
        ],
        "urgency": "Medium — Resolve within shift to prevent thermal degradation",
        "estimated_downtime_minutes": 15,
    },
    "Excessive Vibration": {
        "severity": "WARNING",
        "short_action": "Inspect motor baseplate fasteners, flexible shaft coupling, and dynamic rotor balance.",
        "root_causes": [
            "Loose mounting bolts on the motor chassis.",
            "Shaft angular or parallel misalignment relative to the driven load.",
            "Dynamic imbalance on rotating pulley, gear, or cooling fan.",
            "Early stage bearing race pit or ball defect."
        ],
        "checklist": [
            "Torque all chassis mounting bolts to manufacturer specifications.",
            "Use dial indicators or alignment shims to verify shaft collinearity.",
            "Inspect rotating fan blades or pulleys for chipped edges or eccentricity.",
            "Perform acoustic bearing check with stethoscope or contact probe."
        ],
        "urgency": "Medium — Inspect before next operational cycle",
        "estimated_downtime_minutes": 20,
    },
    "Motor Overheating": {
        "severity": "CRITICAL",
        "short_action": "Immediately de-energize motor or reduce duty cycle; inspect forced air cooling and ambient thermal environment.",
        "root_causes": [
            "Prolonged operation under high continuous armature current.",
            "Obstructed cooling vents or fan failure.",
            "High ambient operating temperature (>45°C) reducing heat dissipation.",
            "Internal winding insulation deterioration leading to eddy current heating."
        ],
        "checklist": [
            "Safely de-energize and allow stator windings to cool below 45°C.",
            "Clean motor housing cooling fins and clear dust filters.",
            "Verify DS18B20 thermal contact pad and thermal paste integrity.",
            "Check winding resistance with multimeter to rule out shorted turns."
        ],
        "urgency": "High — Immediate action required to prevent winding insulation burnout",
        "estimated_downtime_minutes": 30,
    },
    "Motor Stall": {
        "severity": "CRITICAL",
        "short_action": "IMMEDIATE EMERGENCY SHUTDOWN: De-energize L298N driver to prevent locked-rotor winding burnout.",
        "root_causes": [
            "Complete mechanical lock of the driven mechanism.",
            "Severe internal gearbox teeth fracture or bearing seizure.",
            "Sudden overload torque exceeding motor locked-rotor stall torque."
        ],
        "checklist": [
            "Immediately disable H-Bridge enable pin (ENA/ENB on L298N).",
            "Disconnect power supply and inspect for mechanical obstruction.",
            "Check L298N driver heatsink for thermal stress or damage.",
            "Verify DC power supply overcurrent protection tripped as intended."
        ],
        "urgency": "CRITICAL — Emergency stop",
        "estimated_downtime_minutes": 45,
    },
    "Motor Slowdown": {
        "severity": "WARNING",
        "short_action": "Inspect DC supply voltage under load and check for incipient mechanical friction.",
        "root_causes": [
            "Supply rail voltage sag under load due to high source impedance.",
            "Partial mechanical drag on driven conveyor.",
            "Brush wear or commutator oxidation in brushed DC motor."
        ],
        "checklist": [
            "Measure 12V terminal voltage across motor leads under running load.",
            "Inspect optical tachometer disc for dust or misalignment.",
            "Check carbon brush contact pressure and commutator surface condition."
        ],
        "urgency": "Medium — Schedule maintenance within 24 hours",
        "estimated_downtime_minutes": 15,
    },
    "Sensor Error": {
        "severity": "UNKNOWN / SENSOR ERROR",
        "short_action": "Inspect sensor harness, I2C bus pullups, OneWire pullup resistor, and ADC analog ground.",
        "root_causes": [
            "Loose DuPont wire on MPU6050 SDA/SCL or DS18B20 DQ pin.",
            "Missing 4.7kΩ pull-up resistor on DS18B20 OneWire line.",
            "Electromagnetic interference (EMI) coupling from motor PWM into ADC.",
            "ACS712 zero-current offset drift or loose analog input connection."
        ],
        "checklist": [
            "Inspect physical wiring headers and ensure tight breadboard/screw terminal connection.",
            "Confirm common ground between 12V motor supply and ESP32 3.3V/GND.",
            "Check 3.3V logic supply rail stability with multimeter or oscilloscope.",
            "Re-calibrate ACS712 Vref with motor de-energized."
        ],
        "urgency": "High — Monitoring fidelity is compromised",
        "estimated_downtime_minutes": 10,
    },
}


def get_recommendation_for_fault(fault_name: str) -> Dict[str, Any]:
    """Returns detailed maintenance recommendations and checklist for a fault."""
    for key, data in FAULT_RECOMMENDATIONS.items():
        if key.lower() in fault_name.lower():
            return data
    # Fallback
    return {
        "severity": "WARNING",
        "short_action": "Perform physical inspection of motor asset and cross-reference multi-sensor readings.",
        "root_causes": ["Unclassified operational anomaly detected."],
        "checklist": ["Inspect mechanical coupling.", "Check electrical connections.", "Review telemetry trend logs."],
        "urgency": "Medium",
        "estimated_downtime_minutes": 15,
    }
