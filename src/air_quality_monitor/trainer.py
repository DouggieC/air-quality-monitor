import logging
from datetime import datetime
from math import sqrt

import joblib
import jsonlines
import pandas as pd
from lightgbm import LGBMRegressor
from scipy.stats import randint, uniform
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import RandomizedSearchCV
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
        X_train, y_train, _, _, X_test, y_test = self._load_data()

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

        for range_name, horizons in horizon_ranges.items():
            mask_train = X_train["horizon"].isin(horizons)
            mask_test = X_test["horizon"].isin(horizons)

            X_train_range = X_train.loc[mask_train]
            y_train_range = y_train.loc[mask_train]
            X_test_range = X_test.loc[mask_test]
            y_test_range = y_test.loc[mask_test]

            for name, model in models.items():
                self.logger.info(f"Training {name} on {range_name} range horizon")
                model.fit(X_train_range, y_train_range)

                self.logger.info(f"Testing {name} on {range_name} range horizon")
                y_pred_range = model.predict(X_test_range)

                self.logger.info(f"Calculating metrics for {name} on {range_name} range horizon")
                rmse = sqrt(mean_squared_error(y_test_range, y_pred_range))
                mae = mean_absolute_error(y_test_range, y_pred_range)
                r2 = r2_score(y_test_range, y_pred_range)

                self.logger.info(f"Metrics for {name} on {range_name} range horizon")
                self.logger.info(f"RMSE:\t{rmse}")
                self.logger.info(f"MAE:\t{mae}")
                self.logger.info(f"R^2 Score:\t{r2}")

                within_5 = (abs(y_test_range - y_pred_range) <= 5).mean() * 100
                within_10 = (abs(y_test_range - y_pred_range) <= 10).mean() * 100
                within_20 = (abs(y_test_range - y_pred_range) <= 20).mean() * 100

                self.logger.info(f"Predictions within 5 AQI points of actual:\t{within_5}")
                self.logger.info(f"Predictions within 10 AQI points of actual:\t{within_10}")
                self.logger.info(f"Predictions within 20 AQI points of actual:\t{within_20}")

                self.logger.info(f"Saving {name} on {range_name} range horizon")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # noqa: DTZ005
                filename = f"{name}_{range_name}_{timestamp}.joblib"
                joblib.dump(model, Config.MODELS_DIR / filename)

                self.logger.info(f"Saving experiment details for {name} on {range_name} range horizon")
                hyperparams = model.get_params()
                metrics = {
                    "rmse": rmse,
                    "mae": mae,
                    "r2": r2,
                    "within_5": within_5,
                    "within_10": within_10,
                    "within_20": within_20,
                }

                self._log_experiment(f"{name}_{range_name}", timestamp, hyperparams, metrics)

    def tune(self):
        self.logger.debug("Executing Method")

        self.logger.debug("Loading training data")
        X_train, y_train, X_val, y_val, X_test, y_test = self._load_data(include_validation=True)

        # Define hyperparameter ranges
        param_dist = {
            "n_estimators": randint(100, 1000),  # The number of trees to build
            "learning_rate": uniform(0.01, 0.29),  # Step size
            "max_depth": randint(3, 12),  # Tree depth
            "num_leaves": randint(15, 127),  #
            "min_child_samples": randint(5, 50),  # Min samples per leaf
            "subsample": uniform(0.6, 0.4),  # Row sampling
            "colsample_bytree": uniform(0.6, 0.4),  # Feature sampling
            "reg_alpha": uniform(0, 1),  # L1 regularisation
            "reg_lambda": uniform(0, 1),  # L2 regularisation
        }

        search = RandomizedSearchCV(
            LGBMRegressor(),
            param_distributions=param_dist,
            n_iter=50,
            cv=5,
            scoring="neg_root_mean_squared_error",
            random_state=42,
            n_jobs=1,
        )

        self.logger.info("Tuning hyperparameters")
        search.fit(X_train, y_train)

        print(f"Best params:\n{search.best_params_}")
        print(f"Best score:\t{search.best_score_}")

    def _load_data(self, include_validation=False):
        self.logger.debug("Executing method")
        self.logger.debug("Reading data")
        df = pd.read_csv(self.data_path)

        # Sort chronologically
        self.logger.debug("Sorting data")
        df = df.sort_values(by="collected_at")

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

        return X_train, y_train, X_val, y_val, X_test, y_test

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
