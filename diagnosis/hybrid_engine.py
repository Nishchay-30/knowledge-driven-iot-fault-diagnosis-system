"""
Hybrid Diagnostic Engine Module
Combines deterministic physics-based expert rules with probabilistic machine learning predictions.
Transparently flags conflicts, aggregates confidence, and yields prescriptive maintenance actions.
"""

from typing import Dict, Any, List, Optional
from diagnosis.rule_engine import rule_engine
from ml.predict import predictor


SEVERITY_ORDER = {
    "NORMAL": 0,
    "WARNING": 1,
    "CRITICAL": 2,
    "UNKNOWN / SENSOR ERROR": 3,
}

FAULT_TO_SEVERITY = {
    "Normal": "NORMAL",
    "Mechanical Overload": "WARNING",
    "Excessive Vibration": "WARNING",
    "Motor Slowdown": "WARNING",
    "Motor Overheating": "CRITICAL",
    "Motor Stall": "CRITICAL",
    "Motor Stall / Locked Rotor": "CRITICAL",
    "Sensor Error": "UNKNOWN / SENSOR ERROR",
    "Sensor Acquisition Fault": "UNKNOWN / SENSOR ERROR",
}


class HybridDiagnosticEngine:
    """
    Reconciles Rule Engine evaluation with Random Forest ML inference.
    """

    def __init__(self, rule_eng=rule_engine, ml_pred=predictor):
        self.rule_engine = rule_eng
        self.ml_predictor = ml_pred

    def diagnose(
        self,
        reading: Dict[str, Any],
        recent_history: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Runs both diagnostic paradigms and synthesizes an explainable hybrid decision.
        """
        # 1. Evaluate Rule-based Knowledge Base
        rule_result = self.rule_engine.evaluate(reading)
        rule_fault = rule_result["suspected_fault"]
        rule_sev = rule_result["severity"]
        rule_conf = rule_result["confidence"]

        # 2. Evaluate ML Classifier
        ml_fault, ml_conf, ml_probs = self.ml_predictor.predict(reading, recent_history)

        # 3. Conflict Detection & Reconciliation
        conflict_detected = False
        reconciliation_notes = ""

        # Normalize naming for comparison
        norm_rule = "Sensor Error" if "Sensor" in rule_fault else (
            "Motor Stall" if "Stall" in rule_fault else rule_fault
        )
        norm_ml = "Sensor Error" if ml_fault and "Sensor" in ml_fault else (
            "Motor Stall" if ml_fault and "Stall" in ml_fault else ml_fault
        )

        if ml_fault is None:
            # ML offline fallback
            hybrid_fault = rule_fault
            hybrid_sev = rule_sev
            hybrid_conf = rule_conf
            reconciliation_notes = "ML model unavailable. Operating in deterministic rules-only mode."
        elif norm_rule == norm_ml:
            # Unanimous agreement
            hybrid_fault = rule_fault
            hybrid_sev = rule_sev
            # Boost confidence when both agree
            hybrid_conf = round(min(0.99, (rule_conf + ml_conf) / 2.0 + 0.05), 4)
            reconciliation_notes = f"Unanimous consensus between Physics Rules and ML Classifier (Confidence: {hybrid_conf*100:.1f}%)."
        else:
            # Conflict detected
            conflict_detected = True
            ml_sev = FAULT_TO_SEVERITY.get(ml_fault, "WARNING")
            
            # Conservative safety rule: choose highest severity hypothesis
            rule_sev_rank = SEVERITY_ORDER.get(rule_sev, 1)
            ml_sev_rank = SEVERITY_ORDER.get(ml_sev, 1)

            if rule_sev_rank >= ml_sev_rank:
                hybrid_fault = rule_fault
                hybrid_sev = rule_sev
            else:
                hybrid_fault = ml_fault
                hybrid_sev = ml_sev

            # Uncertainty penalty
            hybrid_conf = round(max(0.40, min(rule_conf, ml_conf) * 0.85), 4)
            reconciliation_notes = (
                f"Diagnostic Conflict: Rule Engine indicated '{rule_fault}' ({rule_sev}), "
                f"while ML predicted '{ml_fault}' ({ml_sev}, p={ml_conf:.2f}). "
                f"Selected '{hybrid_fault}' under industrial safety conservatism."
            )

        return {
            "device_id": reading.get("device_id", "motor01"),
            "event_id": reading.get("event_id", ""),
            "timestamp": reading.get("timestamp", ""),
            "rule_fault": rule_fault,
            "rule_severity": rule_sev,
            "ml_fault": ml_fault or "N/A",
            "ml_confidence": ml_conf,
            "hybrid_fault": hybrid_fault,
            "hybrid_severity": hybrid_sev,
            "hybrid_confidence": hybrid_conf,
            "explanation": f"{rule_result['explanation']} {reconciliation_notes}",
            "recommended_action": rule_result["recommended_action"],
            "conflict_detected": conflict_detected,
            "triggering_evidence": rule_result["triggering_evidence"],
            "activated_rules": rule_result["activated_rules"],
            "ml_probabilities": ml_probs,
        }


hybrid_engine = HybridDiagnosticEngine()

