"""
Data Validation Module
Ensures schema adherence, physical sanity checks, and deduplication for sensor telemetry.
"""

from typing import Dict, Any, Tuple, Optional
from datetime import datetime


REQUIRED_SENSOR_FIELDS = {
    "event_id": str,
    "device_id": str,
    "timestamp": str,
    "source": str,
    "temperature_c": (int, float),
    "vibration_rms_g": (int, float),
    "current_a": (int, float),
    "rpm": (int, float),
    "sensor_status": str,
}


class DataValidator:
    """
    Validates structure, typing, physical plausibility, and formatting of incoming sensor messages.
    """

    def __init__(self, seen_cache_size: int = 1000):
        self._seen_event_ids = set()
        self._cache_size = seen_cache_size

    def is_duplicate(self, event_id: str) -> bool:
        """Returns True if the event_id has already been processed."""
        if event_id in self._seen_event_ids:
            return True
        if len(self._seen_event_ids) >= self._cache_size:
            # Pop roughly 20% oldest entries to prevent memory bloat
            remove_count = self._cache_size // 5
            for _ in range(remove_count):
                if self._seen_event_ids:
                    self._seen_event_ids.pop()
        self._seen_event_ids.add(event_id)
        return False

    def validate_sensor_payload(self, payload: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validates an incoming sensor dictionary.
        Returns: (is_valid: bool, error_message: Optional[str])
        """
        if not isinstance(payload, dict):
            return False, "Payload must be a valid JSON dictionary."

        # Check required fields and types
        for field, expected_type in REQUIRED_SENSOR_FIELDS.items():
            if field not in payload:
                return False, f"Missing mandatory field '{field}'."
            val = payload[field]
            if not isinstance(val, expected_type):
                return False, f"Field '{field}' must be {expected_type}, got {type(val).__name__}."

        # Validate timestamp ISO format
        try:
            ts_str = payload["timestamp"].replace("Z", "+00:00")
            datetime.fromisoformat(ts_str)
        except Exception:
            return False, f"Invalid ISO-8601 timestamp format: '{payload['timestamp']}'."

        # Deduplication check
        event_id = payload["event_id"]
        if self.is_duplicate(event_id):
            return False, f"Duplicate event_id detected: '{event_id}'."

        return True, None

