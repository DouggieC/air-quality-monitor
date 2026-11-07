import json

from fastapi import FastAPI

from .config import Config
from .models import City, Prediction
from .storage import CSVStorage, DBStorage
from .storage_factory import StorageFactory


def _get_storage():
    sf = StorageFactory(Config)
    pred_csv, pred_db = sf.get_storage(Prediction)
    return pred_db or pred_csv


pred_storage = _get_storage()

app = FastAPI()


@app.get("/cities")
def get_cities():
    with open(Config.CONFIG_DIR / "cities.json") as f:
        cities = json.load(f)
    return {"cities": [c["city"] for c in cities]}


@app.get("/metrics")
def get_metrics():
    with open(Config.CONFIG_DIR / "model_metrics.json") as f:
        metrics = json.load(f)
    return metrics


@app.get("/predictions/{city}")
def get_predictions(city: str):
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
    predictions = pred_storage.read()
    latest = predictions["collected_at"].max()
    return {"latest_prediction": latest.isoformat()}
