"""
Knowledge Base Management & Query Interface.
Loads, validates, and provides structured query access to declarative engineering rules
and operational threshold envelopes.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml

from config.settings import settings


class KnowledgeBaseManager:
    """
    Manages loading, validating, and querying domain knowledge rules from YAML configuration.
    """

    def __init__(self, kb_path: Optional[Path] = None, thresholds_path: Optional[Path] = None):
        self.kb_path = Path(kb_path or settings.KNOWLEDGE_BASE_FILE)
        self.thresholds_path = Path(thresholds_path or settings.THRESHOLDS_FILE)
        self._rules: List[Dict[str, Any]] = []
        self._metadata: Dict[str, Any] = {}
        self._thresholds: Dict[str, Any] = {}
        self.reload()

    def reload(self) -> None:
        """Loads or reloads knowledge base and thresholds from YAML files."""
        if self.kb_path.exists():
            with open(self.kb_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                self._metadata = data.get("metadata", {})
                self._rules = data.get("rules", [])
                self._rules.sort(key=lambda r: r.get("priority", 0), reverse=True)

        if self.thresholds_path.exists():
            with open(self.thresholds_path, "r", encoding="utf-8") as f:
                self._thresholds = yaml.safe_load(f) or {}

    @property
    def rules(self) -> List[Dict[str, Any]]:
        return self._rules

    @property
    def metadata(self) -> Dict[str, Any]:
        return self._metadata

    @property
    def thresholds(self) -> Dict[str, Any]:
        return self._thresholds

    def get_rule_by_id(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a specific rule by its unique identifier."""
        for r in self._rules:
            if r.get("rule_id") == rule_id:
                return r
        return None

    def get_rules_by_severity(self, severity: str) -> List[Dict[str, Any]]:
        """Filters rules by output severity level (e.g. CRITICAL, WARNING, NORMAL)."""
        return [
            r for r in self._rules
            if r.get("hypothesis", {}).get("severity", "").upper() == severity.upper()
        ]

    def describe(self) -> Dict[str, Any]:
        """Returns statistical overview of the loaded knowledge base."""
        return {
            "title": self._metadata.get("title", "Motor Fault Knowledge Base"),
            "version": self._metadata.get("version", "1.0.0"),
            "target_motor": self._metadata.get("target_motor", "12V DC Motor"),
            "total_rules": len(self._rules),
            "rule_ids": [r.get("rule_id") for r in self._rules],
            "severities": list(set(r.get("hypothesis", {}).get("severity") for r in self._rules)),
        }


# Singleton instance
kb_manager = KnowledgeBaseManager()
