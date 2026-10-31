"""
FastAPI Backend API Application.
Provides authenticated REST endpoints for sensor telemetry, historical analytics,
alerts management, system health, and simulation scenario controls.
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, HTTPException, Header, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config.settings import settings
from database.repository import repo
from backend.auth.security import auth_manager
from ml.predict import predictor

app = FastAPI(
    title="Knowledge-Driven IoT Fault Diagnosis API",
    version="1.0.0",
    description="REST API for 12V Industrial DC Motor Telemetry, Expert Rules & AI Diagnosis",
)

# CORS middleware for Streamlit / external UI integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request Models ---
class LoginRequest(BaseModel):
    username: str
    password: str


class ScenarioRequest(BaseModel):
    device_id: str = "motor01"
    scenario: str


class AlertAckRequest(BaseModel):
    username: Optional[str] = "operator"


# --- Dependency: Auth Header Validation ---
def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization Header")
    token = authorization.replace("Bearer ", "").strip()
    session = auth_manager.validate_session(token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session token")
    return session


# --- Health & Status ---
@app.get("/api/health")
def get_health():
    mqtt_cfg = settings.get_effective_mqtt_config()
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "operation_mode": settings.OPERATION_MODE,
        "mqtt_broker": {
            "type": mqtt_cfg["broker_type"],
            "host": mqtt_cfg["host"],
            "port": mqtt_cfg["port"],
            "tls": mqtt_cfg["use_tls"],
        },
        "database": {
            "type": "SQLite WAL",
            "path": str(settings.DATABASE_PATH),
            "accessible": settings.DATABASE_PATH.exists(),
        },
        "ml_model": {
            "loaded": predictor.is_loaded,
            "classes": predictor.classes,
        },
    }


# --- Authentication ---
@app.post("/api/auth/login")
def login(req: LoginRequest):
    res = auth_manager.authenticate_user(req.username, req.password)
    if not res:
        raise HTTPException(status_code=401, detail="Invalid credentials or inactive account")
    if "error" in res:
        raise HTTPException(status_code=429, detail=res["error"])
    return res


@app.post("/api/auth/logout")
def logout(authorization: Optional[str] = Header(None)):
    if authorization:
        token = authorization.replace("Bearer ", "").strip()
        auth_manager.logout_session(token)
    return {"message": "Logged out successfully"}


# --- Telemetry & Diagnostics ---
@app.get("/api/telemetry/recent")
def get_recent_telemetry(
    device_id: str = "motor01",
    limit: int = Query(default=50, le=500),
):
    df = repo.get_recent_readings(device_id=device_id, limit=limit)
    return df.to_dict(orient="records")


@app.get("/api/telemetry/history")
def get_telemetry_history(
    device_id: str = "motor01",
    start_time: str = Query(..., description="ISO UTC Start"),
    end_time: str = Query(..., description="ISO UTC End"),
    limit: int = Query(default=1000, le=5000),
):
    df = repo.get_readings_by_time_range(device_id, start_time, end_time, limit)
    return df.to_dict(orient="records")


@app.get("/api/diagnosis/recent")
def get_recent_diagnoses(
    device_id: str = "motor01",
    limit: int = Query(default=20, le=100),
):
    df = repo.get_recent_predictions(device_id=device_id, limit=limit)
    return df.to_dict(orient="records")


# --- Alerts Management ---
@app.get("/api/alerts")
def get_alerts(
    device_id: Optional[str] = None,
    unacknowledged_only: bool = False,
    limit: int = 50,
):
    df = repo.get_alerts(device_id=device_id, only_unacknowledged=unacknowledged_only, limit=limit)
    return df.to_dict(orient="records")


@app.post("/api/alerts/{alert_id}/ack")
def acknowledge_alert(
    alert_id: int,
    req: AlertAckRequest,
    user: Dict[str, Any] = Depends(get_current_user),
):
    username = user.get("username", req.username)
    ok = repo.acknowledge_alert(alert_id, user=username)
    if not ok:
        raise HTTPException(status_code=404, detail="Alert not found or update failed")
    return {"message": f"Alert {alert_id} acknowledged by {username}"}


# --- Model Evaluation Metrics ---
@app.get("/api/model/metrics")
def get_model_metrics():
    import json
    if not settings.ML_METRICS_PATH.exists():
        raise HTTPException(status_code=404, detail="Model metrics file not found")
    with open(settings.ML_METRICS_PATH, "r", encoding="utf-8") as f:
        metrics = json.load(f)
    cm = {}
    if settings.ML_CONFUSION_MATRIX_PATH.exists():
        with open(settings.ML_CONFUSION_MATRIX_PATH, "r", encoding="utf-8") as f:
            cm = json.load(f)
    return {"metrics": metrics, "confusion_matrix": cm}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=False)

