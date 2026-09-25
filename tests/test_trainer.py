from unittest.mock import patch

import pandas as pd
import pytest

from air_quality_monitor.trainer import Trainer


class TestTrainer:
    def test_load_data(self, sample_training_df):
        with patch("air_quality_monitor.trainer.pd.read_csv", return_value=sample_training_df):
            trainer = Trainer()
            X_train, y_train, X_test, y_test = trainer._load_data()

            # Check we have the correct data types
            assert isinstance(X_train, pd.DataFrame)
            assert isinstance(X_test, pd.DataFrame)
            assert isinstance(y_train, pd.Series)
            assert isinstance(y_test, pd.Series)

            # Check we have a 70/30 split of the data
            assert len(X_train) == pytest.approx(len(sample_training_df) * 0.7, rel=1e-2)
            assert len(X_test) == pytest.approx(len(sample_training_df) * 0.3, rel=1e-2)
