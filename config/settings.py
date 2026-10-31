"""
Configuration and Environment Settings Module
Provides centralized, strongly-typed settings with automatic local broker fallback.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Base Directory Resolution
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Settings:
    # Base paths
    PROJECT_ROOT: Path = BASE_DIR
    CONFIG_DIR: Path = BASE_DIR / "config"
    DATA_DIR: Path = BASE_DIR / "data"
    CSV_DIR: Path = DATA_DIR / "csv"
    SQLITE_DIR: Path = DATA_DIR / "sqlite"
    SYNTHETIC_DIR: Path = DATA_DIR / "synthetic"
    MODELS_DIR: Path = BASE_DIR / "ml" / "models"
    DOCS_DIR: Path = BASE_DIR / "docs"

    # Environment & Device
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "default-dev-secret-key-change-in-production-12345678")
    OPERATION_MODE: str = os.getenv("OPERATION_MODE", "simulation").lower()
    DEVICE_ID: str = os.getenv("DEVICE_ID", "motor01")

    # MQTT Settings
    USE_LOCAL_BROKER: bool = os.getenv("USE_LOCAL_BROKER", "true").lower() in ("true", "1", "yes")
    LOCAL_MQTT_HOST: str = os.getenv("LOCAL_MQTT_HOST", "127.0.0.1")
    LOCAL_MQTT_PORT: int = int(os.getenv("LOCAL_MQTT_PORT", "1883"))

    # HiveMQ Cloud Settings
    HIVEMQ_HOST: Optional[str] = os.getenv("HIVEMQ_HOST", "").strip() or None
    HIVEMQ_PORT: int = int(os.getenv("HIVEMQ_PORT", "8883"))
    HIVEMQ_USERNAME: Optional[str] = os.getenv("HIVEMQ_USERNAME", "").strip() or None
    HIVEMQ_PASSWORD: Optional[str] = os.getenv("HIVEMQ_PASSWORD", "").strip() or None
    HIVEMQ_USE_TLS: bool = os.getenv("HIVEMQ_USE_TLS", "true").lower() in ("true", "1", "yes")

    # Storage Paths
    DATABASE_PATH: Path = BASE_DIR / os.getenv("DATABASE_PATH", "data/sqlite/fault_diagnosis.db")
    CSV_LOG_PATH: Path = BASE_DIR / os.getenv("CSV_LOG_PATH", "data/csv/sensor_telemetry.csv")
    INGESTION_PATH: str = os.getenv("INGESTION_PATH", "mqtt").lower()

    # REST API & Dashboard
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    DASHBOARD_PORT: int = int(os.getenv("DASHBOARD_PORT", "8501"))

    # Node-RED
    NODERED_ENABLED: bool = os.getenv("NODERED_ENABLED", "true").lower() in ("true", "1", "yes")
    NODERED_HOST: str = os.getenv("NODERED_HOST", "127.0.0.1")
    NODERED_PORT: int = int(os.getenv("NODERED_PORT", "1880"))
    NODERED_API_URL: str = os.getenv("NODERED_API_URL", "http://127.0.0.1:1880")

    # ML Paths
    ML_MODEL_PATH: Path = BASE_DIR / os.getenv("ML_MODEL_PATH", "ml/models/random_forest_model.joblib")
    ML_METRICS_PATH: Path = BASE_DIR / os.getenv("ML_METRICS_PATH", "ml/models/model_metrics.json")
    ML_CONFUSION_MATRIX_PATH: Path = BASE_DIR / os.getenv("ML_CONFUSION_MATRIX_PATH", "ml/models/confusion_matrix.json")

    # Config File Paths
    THRESHOLDS_FILE: Path = BASE_DIR / "config" / "thresholds.yaml"
    DEVICES_FILE: Path = BASE_DIR / "config" / "devices.yaml"
    KNOWLEDGE_BASE_FILE: Path = BASE_DIR / "config" / "knowledge_base.yaml"

    @property
    def is_hivemq_configured(self) -> bool:
        """Returns True only if valid non-empty HiveMQ host and credentials exist."""
        return bool(
            self.HIVEMQ_HOST
            and not self.USE_LOCAL_BROKER
            and self.HIVEMQ_USERNAME
            and self.HIVEMQ_PASSWORD
        )

    def get_effective_mqtt_config(self) -> dict:
        """
        Determines whether to use HiveMQ Cloud or fall back to local broker.
        Never throws when cloud credentials are unconfigured.
        """
        if self.is_hivemq_configured:
            return {
                "broker_type": "hivemq_cloud",
                "host": self.HIVEMQ_HOST,
                "port": self.HIVEMQ_PORT,
                "username": self.HIVEMQ_USERNAME,
                "password": self.HIVEMQ_PASSWORD,
                "use_tls": self.HIVEMQ_USE_TLS,
            }
        return {
            "broker_type": "local_fallback",
            "host": self.LOCAL_MQTT_HOST,
            "port": self.LOCAL_MQTT_PORT,
            "username": None,
            "password": None,
            "use_tls": False,
        }

    # MQTT Topic Helpers
    @staticmethod
    def get_sensor_topic(device_id: str = "motor01") -> str:
        return f"iot/factory/{device_id}/sensors"

    @staticmethod
    def get_status_topic(device_id: str = "motor01") -> str:
        return f"iot/factory/{device_id}/status"

    @staticmethod
    def get_ground_truth_topic(device_id: str = "motor01") -> str:
        return f"iot/factory/{device_id}/ground_truth"

    @staticmethod
    def get_diagnosis_topic(device_id: str = "motor01") -> str:
        return f"iot/factory/{device_id}/diagnosis"

    @staticmethod
    def get_alerts_topic(device_id: str = "motor01") -> str:
        return f"iot/factory/{device_id}/alerts"

    @staticmethod
    def get_commands_topic(device_id: str = "motor01") -> str:
        return f"iot/factory/{device_id}/commands"

    @staticmethod
    def get_command_ack_topic(device_id: str = "motor01") -> str:
        return f"iot/factory/{device_id}/command_ack"


settings = Settings()

# Ensure directories exist
for directory in [
    settings.DATA_DIR,
    settings.CSV_DIR,
    settings.SQLITE_DIR,
    settings.SYNTHETIC_DIR,
    settings.MODELS_DIR,
]:
    directory.mkdir(parents=True, exist_ok=True)

