"""
REST API for the AQI prediction website.

FastAPI endpoints serving prediction data, city lists, and model metrics
to the frontend. Runs on the collector Pi behind Cloudflare Tunnel.
"""

import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import Config
from .models import City, Prediction
from .storage import CSVStorage, DBStorage
from .storage_factory import StorageFactory


def _get_storage():
    """Initialize prediction storage backend (DB preferred over CSV)."""
    sf = StorageFactory(Config)
    pred_csv, pred_db = sf.get_storage(Prediction)
    return pred_db or pred_csv


pred_storage = _get_storage()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080"],
    allow_methods=["GET"],
)

@app.get("/cities")
def get_cities():
    """Return list of city names for the dropdown selector."""
    with open(Config.CONFIG_DIR / "cities.json") as f:
        cities = json.load(f)
    return {"cities": [c["city"] for c in cities]}


@app.get("/metrics")
def get_metrics():
    """Return model performance metrics from latest training run."""
    with open(Config.CONFIG_DIR / "model_metrics.json") as f:
        metrics = json.load(f)
    return metrics


@app.get("/predictions/{city}")
def get_predictions(city: str):
    """Return latest predictions for a city (horizons 2h+)."""
    predictions = pred_storage.read()
    predictions = predictions[predictions["city"] == city]
    latest = predictions["collected_at"].max()
    predictions = predictions[(predictions["collected_at"] == latest) & (predictions["horizon"] >= 2)]
    predictions.drop(
        columns=["id", "model_name", "state", "country", "latitude", "longitude", "timezone"], inplace=True
    )
    predictions = predictions.sort_values(by="horizon")
    return predictions.to_dict(orient="records")


@app.get("/status")
def get_status():
    """Return timestamp of most recent prediction for freshness check."""
    predictions = pred_storage.read()
    latest = predictions["collected_at"].max()
    return {"latest_prediction": latest.isoformat()}
