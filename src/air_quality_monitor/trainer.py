import hashlib
import logging
from datetime import datetime
from math import sqrt

import joblib
import jsonlines
import mlflow
import pandas as pd
from lightgbm import LGBMRegressor
from scipy.stats import randint, uniform
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# from sklearn.model_selection import RandomizedSearchCV
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
        X_train, y_train, _, _, X_test, y_test, data_hash = self._load_data()

        self.logger.debug("Splitting on horizons")
        horizon_ranges = {
            "short": [0, 1, 2],
            "medium": [4, 8, 12],
            "long": [24, 28],
        }

        models = {
            "lightgbm": LGBMRegressor(),
            "xgboost": XGBRegressor(),
        }

        # Set up MLflow tracing
        mlflow.set_experiment("AQI Prediction")

        for range_name, horizons in horizon_ranges.items():
            mask_train = X_train["horizon"].isin(horizons)
            mask_test = X_test["horizon"].isin(horizons)

            X_train_range = X_train.loc[mask_train]
            y_train_range = y_train.loc[mask_train]
            X_test_range = X_test.loc[mask_test]
            y_test_range = y_test.loc[mask_test]

            for name, model in models.items():
                self.logger.info(f"Training {name} on {range_name} range horizon")

                # Start MLflow run
                mlflow.start_run(run_name=f"{name}_{range_name}")

                # Train the model
                model.fit(X_train_range, y_train_range)

                self.logger.info(f"Testing {name} on {range_name} range horizon")
                y_pred_range = model.predict(X_test_range)

                self.logger.info(f"Calculating metrics for {name} on {range_name} range horizon")
                metrics = self._calculate_metrics(y_test_range, y_pred_range)

                """
                rmse = sqrt(mean_squared_error(y_test_range, y_pred_range))
                mae = mean_absolute_error(y_test_range, y_pred_range)
                r2 = r2_score(y_test_range, y_pred_range)
                within_5 = (abs(y_test_range - y_pred_range) <= 5).mean() * 100
                within_10 = (abs(y_test_range - y_pred_range) <= 10).mean() * 100
                within_20 = (abs(y_test_range - y_pred_range) <= 20).mean() * 100
                """

                self.logger.info(f"Metrics for {name} on {range_name} range horizon")
                self.logger.info(f"RMSE:\t{metrics['rmse']}")
                self.logger.info(f"MAE:\t{metrics['mae']}")
                self.logger.info(f"R^2 Score:\t{metrics['r2']}")
                self.logger.info(f"Predictions within 5 AQI points of actual:\t{metrics['within_5']}")
                self.logger.info(f"Predictions within 10 AQI points of actual:\t{metrics['within_10']}")
                self.logger.info(f"Predictions within 20 AQI points of actual:\t{metrics['within_20']}")

                self.logger.info(f"Saving {name} on {range_name} range horizon")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # noqa: DTZ005
                filename = f"{name}_{range_name}_{timestamp}.joblib"
                joblib.dump(model, Config.MODELS_DIR / filename)

                self.logger.info(f"Saving experiment details for {name} on {range_name} range horizon")
                hyperparams = model.get_params()
                """
                metrics = {
                    "rmse": rmse,
                    "mae": mae,
                    "r2": r2,
                    "within_5": within_5,
                    "within_10": within_10,
                    "within_20": within_20,
                }
                """

                data_params = {
                    "data_version": "2",
                    "data_filename": "training_data_v2.csv",
                    "data_description": "Include wether trend features",
                    "data_hash": data_hash,
                    "n_rows": len(X_train) + len(X_test),
                    "n_features": len(X_train.columns),
                    "features": ",".join(X_train.columns),
                }

                self._log_to_mlflow(metrics, hyperparams, data_params, model, Config.MODELS_DIR / filename)

                """
                mlflow.log_params(data_params)
                mlflow.log_metrics(metrics)
                mlflow.log_params(hyperparams)
                mlflow.log_artifact(Config.MODELS_DIR / filename)
                mlflow.sklearn.log_model(
                    model,
                    "model",
                    skops_trusted_types=[
                        "collections.OrderedDict",
                        "lightgbm.basic.Booster",
                        "lightgbm.sklearn.LGBMRegressor",
                        "xgboost.core.Booster",
                        "xgboost.sklearn.XGBRegressor",
                    ],
                )
                """
                self._log_experiment(f"{name}_{range_name}", timestamp, hyperparams, metrics)

                mlflow.end_run()

    def tune(self):
        self.logger.debug("Executing Method")

        self.logger.debug("Loading training data")
        X_train, y_train, X_val, y_val, X_test, y_test, data_hash = self._load_data(include_validation=True)

        # Set up MLflow tracing
        mlflow.set_experiment("Model Tuning")

        # Define hyperparameter ranges
        param_dist = {
            "n_estimators": randint(100, 1000),  # The number of trees to build
            "learning_rate": uniform(0.01, 0.29),  # Step size
            "max_depth": randint(3, 12),  # Tree depth
            "num_leaves": randint(15, 127),  # What is this?
            "min_child_samples": randint(5, 50),  # Min samples per leaf
            "subsample": uniform(0.6, 0.4),  # Row sampling
            "colsample_bytree": uniform(0.6, 0.4),  # Feature sampling
            "reg_alpha": uniform(0, 1),  # L1 regularisation
            "reg_lambda": uniform(0, 1),  # L2 regularisation
        }

        best_rmse = {"rmse": float("inf"), "params": {}}
        best_mae = {"mae": float("inf"), "params": {}}

        n_iter = 50  # The number of random iterations to try
        for i in range(0, n_iter):
            # Start MLflow run
            mlflow.start_run(run_name=f"lightgbm_{i}")

            # Generate random values for hyperparameters based on distribution
            params = {key: dist.rvs() for key, dist in param_dist.items()}

            model = LGBMRegressor(**params)

            model.fit(X_train, y_train)
            y_pred = model.predict(X_val)
            metrics = self._calculate_metrics(y_val, y_pred)
            # rmse = sqrt(mean_squared_error(y_val, y_pred))
            # mae = mean_absolute_error(y_val, y_pred)

            if metrics["rmse"] < best_rmse["rmse"]:
                best_rmse["rmse"] = metrics["rmse"]
                best_rmse["params"] = params.copy()

            if metrics["mae"] < best_mae["mae"]:
                best_mae["mae"] = metrics["mae"]
                best_mae["params"] = params.copy()

            self._log_to_mlflow(metrics, params)
            mlflow.end_run()

        print(f"Best score (RMSE):\t{best_rmse['rmse']}")
        print(f"Best params (RMSE):\n{best_rmse['params']}")
        print(f"Best score (MAE):\t{best_mae['mae']}")
        print(f"Best params (MAE):\n{best_mae['params']}")

    def _load_data(self, include_validation=False):
        self.logger.debug("Executing method")
        self.logger.debug("Reading data")
        df = pd.read_csv(self.data_path)

        # Sort chronologically
        self.logger.debug("Sorting data")
        df = df.sort_values(by="collected_at")
        hash = hashlib.md5(pd.util.hash_pandas_object(df).values).hexdigest()[:8]

        if include_validation:
            # Split 60/20/20 for hyperparameter tuning
            self.logger.debug("Tuning run. Use validation set.")
            split_idx_train = int(len(df) * 0.6)
            split_idx_test = int(len(df) * 0.8)
            train_df = df.iloc[:split_idx_train].reset_index(drop=True)
            val_df = df.iloc[split_idx_train:split_idx_test].reset_index(drop=True)
            test_df = df.iloc[split_idx_test:].reset_index(drop=True)

            # Validation set included
            X_val = val_df.drop(columns=["aqi", "collected_at"])
            y_val = val_df["aqi"]
        else:
            # Split 70/30 for model training
            self.logger.debug("Training run. No validation set.")
            split_idx = int(len(df) * 0.7)
            train_df = df.iloc[:split_idx].reset_index(drop=True)
            test_df = df.iloc[split_idx:].reset_index(drop=True)

            # No validation set required
            X_val, y_val = None, None

        X_train = train_df.drop(columns=["aqi", "collected_at"])
        y_train = train_df["aqi"]
        X_test = test_df.drop(columns=["aqi", "collected_at"])
        y_test = test_df["aqi"]

        return X_train, y_train, X_val, y_val, X_test, y_test, hash

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

    def _calculate_metrics(self, y_true, y_pred) -> dict:
        self.logger.debug("Executing method")

        metrics = {
            "rmse": sqrt(mean_squared_error(y_true, y_pred)),
            "mae": mean_absolute_error(y_true, y_pred),
            "r2": r2_score(y_true, y_pred),
            "within_5": (abs(y_true - y_pred) <= 5).mean() * 100,
            "within_10": (abs(y_true - y_pred) <= 10).mean() * 100,
            "within_20": (abs(y_true - y_pred) <= 20).mean() * 100,
        }

        return metrics

    def _log_to_mlflow(self, metrics, hyperparams, data_params=None, model=None, artifact_path=None):
        mlflow.log_metrics(metrics)
        mlflow.log_params(hyperparams)
        if data_params:
            mlflow.log_params(data_params)
        if artifact_path:
            mlflow.log_artifact(artifact_path)
        if model:
            mlflow.sklearn.log_model(
                model,
                "model",
                skops_trusted_types=[
                    "collections.OrderedDict",
                    "lightgbm.basic.Booster",
                    "lightgbm.sklearn.LGBMRegressor",
                    "xgboost.core.Booster",
                    "xgboost.sklearn.XGBRegressor",
                ],
            )
