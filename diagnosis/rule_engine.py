"""
Knowledge-Driven Rule Engine
Evaluates declarative physics and engineering rules against incoming motor telemetry.
Provides deterministic, explainable diagnostic hypotheses and recommended actions.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import yaml
from config.settings import settings


class RuleEngine:
    """
    Expert system rule evaluator. Loads declarative rules from YAML,
    ranks by priority, evaluates condition expressions, and resolves conflicts.
    """

    def __init__(self, kb_path: Path = settings.KNOWLEDGE_BASE_FILE):
        self.kb_path = Path(kb_path)
        self.rules: List[Dict[str, Any]] = []
        self.load_knowledge_base()

    def load_knowledge_base(self) -> None:
        """Loads and sorts rules by priority descending."""
        if not self.kb_path.exists():
            raise FileNotFoundError(f"Knowledge base file not found at {self.kb_path}")
        with open(self.kb_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            self.rules = data.get("rules", [])
            # Sort by priority descending (higher priority evaluated first)
            self.rules.sort(key=lambda r: r.get("priority", 0), reverse=True)

    def _eval_condition(self, expr: str, context: Dict[str, Any]) -> bool:
        """
        Safely evaluates condition expression against telemetry context dictionary.
        Only allows numerical comparisons and logical operators.
        """
        # Restrict environment to arithmetic and boolean logic
        safe_names = {
            "temperature_c": context.get("temperature_c", 0.0),
            "vibration_rms_g": context.get("vibration_rms_g", 0.0),
            "current_a": context.get("current_a", 0.0),
            "rpm": context.get("rpm", 0.0),
            "sensor_status": context.get("sensor_status", "ok"),
        }
        try:
            return bool(eval(expr, {"__builtins__": {}}, safe_names))
        except Exception:
            return False

    def evaluate(self, reading: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates a motor telemetry reading against the knowledge base rules.
        Returns the highest-priority triggered hypothesis with full explainability.
        """
        activated_rules = []
        best_hypothesis: Optional[Dict[str, Any]] = None

        for rule in self.rules:
            conds = rule.get("conditions", {})
            matched = False

            if "all" in conds:
                matched = all(self._eval_condition(c, reading) for c in conds["all"])
            elif "any" in conds:
                matched = any(self._eval_condition(c, reading) for c in conds["any"])

            if matched:
                activated_rules.append(rule["rule_id"])
                if best_hypothesis is None:
                    hyp = rule.get("hypothesis", {}).copy()
                    hyp["rule_id"] = rule["rule_id"]
                    hyp["rule_name"] = rule["name"]
                    hyp["priority"] = rule.get("priority", 0)
                    best_hypothesis = hyp

        # If no rule triggered, fallback to indeterminate warning
        if not best_hypothesis:
            best_hypothesis = {
                "rule_id": "DEFAULT_UNKNOWN",
                "rule_name": "Indeterminate Telemetry Profile",
                "suspected_fault": "Indeterminate / Unclassified State",
                "severity": "WARNING",
                "confidence": 0.50,
                "explanation": "Current sensor values do not cleanly match predefined operating envelopes.",
                "recommended_action": "Cross-reference with ML classifier and observe trend trajectory.",
                "priority": 0,
            }

        # Build triggering evidence summary
        evidence = {
            "temperature_c": reading.get("temperature_c"),
            "vibration_rms_g": reading.get("vibration_rms_g"),
            "current_a": reading.get("current_a"),
            "rpm": reading.get("rpm"),
            "sensor_status": reading.get("sensor_status"),
        }

        return {
            "suspected_fault": best_hypothesis["suspected_fault"],
            "severity": best_hypothesis["severity"],
            "confidence": best_hypothesis["confidence"],
            "explanation": best_hypothesis["explanation"],
            "recommended_action": best_hypothesis["recommended_action"],
            "triggering_evidence": evidence,
            "activated_rules": activated_rules,
            "primary_rule_id": best_hypothesis.get("rule_id"),
        }


rule_engine = RuleEngine()

