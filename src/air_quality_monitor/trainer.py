import hashlib
import json
import logging
from datetime import datetime
from math import sqrt

import joblib
import jsonlines
import mlflow
import pandas as pd
from lightgbm import LGBMRegressor
from scipy.stats import loguniform, randint, uniform
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor

from .config import Config


class Trainer:
    def __init__(self, data_version: int, data_filename: str, data_description: str):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug("Creating object")
        self.data_path = Config.TRAINING_DATA_PATH
        self.data_version = data_version
        self.data_filename = data_filename
        self.data_description = data_description

    def train(self):
        self.logger.debug("Executing Method")

        self.logger.debug("Loading training data")
        X_train, y_train, _, _, X_test, y_test, data_params = self._load_data()

        self.logger.debug("Splitting on horizons")
        horizon_ranges = {
            "short": [0, 1, 2],
            "medium": [4, 8, 12],
            "long": [24, 48],
        }

        self.logger.debug("Reading model hyperparameters from config")
        with open(Config.CONFIG_DIR / "model_params.json", "r") as f:
            model_params = json.load(f)

        # Set up MLflow tracing
        mlflow.set_experiment("AQI Prediction")

        for range_name, horizons in horizon_ranges.items():
            mask_train = X_train["horizon"].isin(horizons)
            mask_test = X_test["horizon"].isin(horizons)

            X_train_range = X_train.loc[mask_train]
            y_train_range = y_train.loc[mask_train]
            X_test_range = X_test.loc[mask_test]
            y_test_range = y_test.loc[mask_test]

            models = {
                f"lightgbm_{range_name}": LGBMRegressor(**model_params[f"lightgbm_{range_name}"]),
                f"xgboost_{range_name}": XGBRegressor(**model_params[f"xgboost_{range_name}"]),
            }

            for name, model in models.items():
                self.logger.info(f"Training {name}")

                metrics = self._train_and_log(
                    model,
                    X_train_range,
                    y_train_range,
                    X_test_range,
                    y_test_range,
                    name,
                    model.get_params(),
                    data_params,
                )

                self.logger.info(f"Metrics for {name}")
                self.logger.info(f"RMSE:\t{metrics['rmse']}")
                self.logger.info(f"MAE:\t{metrics['mae']}")
                self.logger.info(f"R^2 Score:\t{metrics['r2']}")
                self.logger.info(f"Predictions within 5 AQI points of actual:\t{metrics['within_5']}")
                self.logger.info(f"Predictions within 10 AQI points of actual:\t{metrics['within_10']}")
                self.logger.info(f"Predictions within 20 AQI points of actual:\t{metrics['within_20']}")

    def tune(self):
        self.logger.debug("Executing Method")

        self.logger.debug("Loading training data")
        X_train, y_train, X_val, y_val, X_test, y_test, data_params = self._load_data(include_validation=True)

        self.logger.debug("Splitting on horizons")
        horizon_ranges = {
            "short": [0, 1, 2],
            "medium": [4, 8, 12],
            "long": [24, 48],
        }

        models = {
            "lightgbm": LGBMRegressor(),
            "xgboost": XGBRegressor(),
        }

        # Set up MLflow tracing
        mlflow.set_experiment("Model Tuning")

        # Define hyperparameter ranges
        param_dist = {
            "n_estimators": randint(50, 1000),  # The number of trees to build
            "learning_rate": loguniform(0.001, 1),  # Step size
            "max_depth": randint(2, 12),  # Tree depth
            "num_leaves": randint(7, 256),  # Number of leaves in full tree (LightGBM)
            "min_child_samples": randint(1, 100),  # Min samples per leaf (LightGBM)
            "min_child_weight": randint(1, 100),  # Min sum of instance weight (hessian)
            "subsample": uniform(0.4, 0.6),  # Row sampling
            "colsample_bytree": uniform(0.4, 0.6),  # Feature sampling
            "reg_alpha": loguniform(1e-3, 1e2),  # L1 regularisation
            "reg_lambda": loguniform(1e-3, 1e2),  # L2 regularisation
        }

        n_iter = 100  # The number of random iterations to try
        for range_name, horizons in horizon_ranges.items():
            mask_train = X_train["horizon"].isin(horizons)
            mask_val = X_val["horizon"].isin(horizons)
            mask_test = X_test["horizon"].isin(horizons)

            X_train_range = X_train.loc[mask_train]
            y_train_range = y_train.loc[mask_train]
            X_val_range = X_val.loc[mask_val]
            y_val_range = y_val.loc[mask_val]
            X_test_range = X_test.loc[mask_test]
            y_test_range = y_test.loc[mask_test]

            for name, model in models.items():
                self.logger.info(f"Tuning {name} on {range_name} range horizon")
                best_rmse = {"rmse": float("inf"), "params": {}}
                best_mae = {"mae": float("inf"), "params": {}}
                for i in range(n_iter):
                    # Generate random values for hyperparameters based on distribution
                    params = {key: dist.rvs() for key, dist in param_dist.items()}

                    model.set_params(**params)

                    metrics = self._train_and_log(
                        model,
                        X_train_range,
                        y_train_range,
                        X_val_range,
                        y_val_range,
                        f"{name}_{i}_{range_name}",
                        params,
                        include_model=False,
                    )

                    if metrics["rmse"] < best_rmse["rmse"]:
                        best_rmse["rmse"] = metrics["rmse"]
                        best_rmse["params"] = params.copy()

                    if metrics["mae"] < best_mae["mae"]:
                        best_mae["mae"] = metrics["mae"]
                        best_mae["params"] = params.copy()

                self.logger.info(f"Best score (RMSE):\t{best_rmse['rmse']}")
                self.logger.info(f"Best params (RMSE):\n{best_rmse['params']}")
                self.logger.info(f"Best score (MAE):\t{best_mae['mae']}")
                self.logger.info(f"Best params (MAE):\n{best_mae['params']}")

                X_train_full = pd.concat([X_train_range, X_val_range], ignore_index=True)
                y_train_full = pd.concat([y_train_range, y_val_range], ignore_index=True)
                self.logger.info(f"Evaluating best {range_name}-term RMSE model")
                metrics_best_rmse = self._train_and_log(
                    model,
                    X_train_full,
                    y_train_full,
                    X_test_range,
                    y_test_range,
                    f"{name}_{range_name}_best_rmse",
                    best_rmse["params"],
                    data_params,
                )
                self.logger.info(f"Evaluating best {range_name}-term MAE model")
                metrics_best_mae = self._train_and_log(
                    model,
                    X_train_full,
                    y_train_full,
                    X_test_range,
                    y_test_range,
                    f"{name}_{range_name}_best_mae",
                    best_mae["params"],
                    data_params,
                )

                self.logger.info(
                    f"Best {range_name}-term RMSE model - Val RMSE: {best_rmse['rmse']:.2f}, Test RMSE: {metrics_best_rmse['rmse']:.2f}"
                )
                self.logger.info(
                    f"Best {range_name}-term MAE model - Val MAE: {best_mae['mae']:.2f}, Test MAE: {metrics_best_mae['mae']:.2f}"
                )

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

        # Build data_params dict for MLflow logging
        data_params = {
            "data_version": self.data_version,
            "data_filename": self.data_filename,
            "data_description": self.data_description,
            "data_hash": hash,
            "n_rows": len(X_train) + len(X_test),
            "n_features": len(X_train.columns),
            "features": ",".join(X_train.columns),
        }

        return X_train, y_train, X_val, y_val, X_test, y_test, data_params

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

    def _log_to_mlflow(
        self, metrics, hyperparams, data_params=None, model=None, reg_model_name=None, artifact_path=None
    ):
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
                registered_model_name=reg_model_name,
                skops_trusted_types=[
                    "collections.OrderedDict",
                    "lightgbm.basic.Booster",
                    "lightgbm.sklearn.LGBMRegressor",
                    "xgboost.core.Booster",
                    "xgboost.sklearn.XGBRegressor",
                ],
            )

    def _train_and_log(
        self,
        model,
        X_train,
        y_train,
        X_test,
        y_test,
        run_name,
        hyperparams,
        data_params=None,
        include_model=True,
    ) -> dict:
        self.logger.debug("Executing method")

        # Start MLflow
        mlflow.start_run(run_name=run_name)

        # Train the model
        self.logger.info(f"Training {run_name}")
        model.fit(X_train, y_train)

        # Predict and metrics
        self.logger.info(f"Testing {run_name}")
        y_pred = model.predict(X_test)
        metrics = self._calculate_metrics(y_test, y_pred)

        # Save artifact
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # noqa: DTZ005
        if include_model:
            self.logger.info(f"Saving {run_name} model")
            filename = f"{run_name}_{timestamp}.joblib"
            joblib.dump(model, Config.MODELS_DIR / filename)

        # MLflow
        self._log_to_mlflow(
            metrics,
            hyperparams,
            data_params,
            model if include_model else None,
            run_name if include_model else None,
            Config.MODELS_DIR / filename if include_model else None,
        )

        # JSON
        self.logger.info(f"Saving experiment details for {run_name} range horizon")
        self._log_experiment(run_name, timestamp, hyperparams, metrics)

        mlflow.end_run()

        return metrics
