import pandas as pd
import pytest

from air_quality_monitor.features import FeatureEngineer
from tests.conftest import MockStorage


class TestFeatureEngineer:
    @pytest.fixture
    def result_df(self, sample_aqi_df, sample_hourly_df):
        aqi_storage = MockStorage(sample_aqi_df)
        weather_storage = MockStorage(sample_hourly_df)
        engineer = FeatureEngineer(aqi_storage, weather_storage)
        return engineer.build()

    def test_returns_dataframe(self, result_df):
        assert isinstance(result_df, pd.DataFrame)

    def test_join(self, result_df):
        # Check both cities are present
        assert "city_Sarajevo" in result_df.columns
        assert "city_London" in result_df.columns

        # Join produces 954 rows
        assert len(result_df) == 954

        # No duplicate cols from bad join
        assert not any("_x" in col or "_y" in col for col in result_df.columns)

    def test_lag_features(self, result_df):
        filtered = result_df[(result_df["city_Sarajevo"] == True) & (result_df["horizon"] == 0)]
        filtered = filtered.sort_values("collected_at")
        row = filtered.iloc[50]

        assert row["aqi_current"] == 50
        assert row["aqi_lag_1h"] == 49
        assert row["aqi_lag_2h"] == 48
        assert row["aqi_lag_4h"] == 46
        assert row["aqi_lag_8h"] == 42
        assert row["aqi_lag_12h"] == 38
        assert row["aqi_lag_24h"] == 26
        assert row["aqi_lag_48h"] == 2

    def test_rolling_features(self, result_df):
        filtered = result_df[(result_df["city_Sarajevo"] == True) & (result_df["horizon"] == 0)]
        filtered = filtered.sort_values("collected_at")
        row = filtered.iloc[50]

        # Expected values gleaned from notebook exploration
        assert row["aqi_rolling_mean_6h"] == 47.5
        assert row["aqi_rolling_std_6h"] == pytest.approx(1.870829)
        assert row["aqi_rolling_mean_24h"] == 38.5

    def test_temporal_features(self, result_df):
        filtered = result_df[(result_df["city_Sarajevo"] == True) & (result_df["horizon"] == 0)]
        filtered = filtered.sort_values("collected_at")
        row = filtered.iloc[50]
        print(filtered.iloc[50]["collected_at"], filtered.iloc[50]["hour"])

        assert row["horizon"] == 0.0
        assert row["hour"] == 23
        assert row["day_of_week"] == 6
        assert row["month"] == 3

    def test_ohe(self, result_df):
        # Check city column has been dropped and replaced with OHE columns
        assert "city" not in result_df
        assert "city_Sarajevo" in result_df and "city_London" in result_df

        dropped_cols = {"city", "main_pollutant"}
        remaining = dropped_cols & set(result_df.columns)
        assert not remaining, f"Undropped columns: {remaining}"

        expected_cols = {"city_Sarajevo", "city_London", "main_pollutant_p2"}
        missing = expected_cols - set(result_df.columns)
        assert not missing, f"Missing columns: {missing}"
