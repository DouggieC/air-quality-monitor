import logging
from datetime import datetime
from math import sqrt

import joblib
import jsonlines
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor

from .config import Config


class Trainer:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug("Creating object")
        self.data_path = Config.TRAINING_DATA_PATH

    def train(self):
        self.logger.debug("Executing Method")

        self.logger.debug("Loading training data")
        X_train, y_train, X_test, y_test = self._load_data()

        models = {
            "lightgbm": LGBMRegressor(),
            "xgboost": XGBRegressor(),
        }

        for name, model in models.items():
            self.logger.info(f"Training {name}")
            model.fit(X_train, y_train)

            self.logger.info(f"Testing {name}")
            y_pred = model.predict(X_test)

            self.logger.info(f"Calculating metrics for {name}")
            rmse = sqrt(mean_squared_error(y_test, y_pred))
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)

            self.logger.info(f"Metrics for {name}")
            self.logger.info(f"RMSE:\t{rmse}")
            self.logger.info(f"MAE:\t{mae}")
            self.logger.info(f"R^2 Score:\t{r2}")

            within_5 = (abs(y_test - y_pred) <= 5).mean() * 100
            within_10 = (abs(y_test - y_pred) <= 10).mean() * 100
            within_20 = (abs(y_test - y_pred) <= 20).mean() * 100

            self.logger.info(f"Predictions within 5 AQI points of actual:\t{within_5}")
            self.logger.info(f"Predictions within 10 AQI points of actual:\t{within_10}")
            self.logger.info(f"Predictions within 20 AQI points of actual:\t{within_20}")

            self.logger.info(f"Saving {name}")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{name}_{timestamp}.joblib"
            joblib.dump(model, Config.MODELS_DIR / filename)

            self.logger.info(f"Saving experiment details for {name}")
            hyperparams = model.get_params()
            metrics = {
                "rmse": rmse,
                "mae": mae,
                "r2": r2,
                "within_5": within_5,
                "within_10": within_10,
                "within_20": within_20,
            }

            self._log_experiment(name, timestamp, hyperparams, metrics)

    def _load_data(self) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
        df = pd.read_csv(self.data_path)

        # Sort chronologically
        df = df.sort_values(by="collected_at")

        # Split 70/30 for train/test
        split_idx = int(len(df) * 0.7)
        train_df = df.iloc[:split_idx].reset_index(drop=True)
        test_df = df.iloc[split_idx:].reset_index(drop=True)

        X_train = train_df.drop(columns=["aqi", "collected_at"])
        y_train = train_df["aqi"]
        X_test = test_df.drop(columns=["aqi", "collected_at"])
        y_test = test_df["aqi"]

        return X_train, y_train, X_test, y_test

    def _log_experiment(self, model_name: str, timestamp: str, hyperparams: dict, metrics: dict):
        self.logger.debug("Executing method")

        record = {
            "timestamp": timestamp,
            "model": model_name,
            "hyperparams": hyperparams,
            "metrics": metrics,
        }

        with jsonlines.open(Config.LOG_DIR / "experiments.jsonl", mode="a") as writer:
            writer.write(record)
