import pytest

from app.services.accuracy_service import (
    AccuracyDataError,
    calculate_accuracy,
)


def test_calculates_hourly_accuracy():
    actuals = [
        {"fuelType": "WIND", "startTime": "2026-01-01T00:00:00Z", "generation": 100},
        {"fuelType": "WIND", "startTime": "2026-01-01T00:30:00Z", "generation": 120},
    ]
    forecasts = [
        {
            "startTime": "2026-01-01T00:00:00Z",
            "publishTime": "2025-12-31T22:30:00Z",
            "generation": 130,
        }
    ]

    result = calculate_accuracy(actuals, forecasts)

    assert result["matchedHours"] == 1
    assert result["hourlyResults"][0]["actual"] == 110
    assert result["hourlyResults"][0]["forecast"] == 130
    assert result["mae"] == 20
    assert result["rmse"] == 20
    assert result["wapePercent"] == pytest.approx(100 * 20 / 110, abs=0.001)


def test_rejects_incomplete_half_hour_pair():
    actuals = [
        {"fuelType": "WIND", "startTime": "2026-01-01T00:00:00Z", "generation": 100}
    ]
    forecasts = [
        {"startTime": "2026-01-01T00:00:00Z", "generation": 100}
    ]

    with pytest.raises(AccuracyDataError, match="Expected 2 half-hour actuals"):
        calculate_accuracy(actuals, forecasts)


def test_rejects_multiple_forecast_vintages():
    actuals = [
        {"fuelType": "WIND", "startTime": "2026-01-01T00:00:00Z", "generation": 100},
        {"fuelType": "WIND", "startTime": "2026-01-01T00:30:00Z", "generation": 100},
        {"fuelType": "WIND", "startTime": "2026-01-01T01:00:00Z", "generation": 100},
        {"fuelType": "WIND", "startTime": "2026-01-01T01:30:00Z", "generation": 100},
    ]
    forecasts = [
        {"startTime": "2026-01-01T00:00:00Z", "publishTime": "2025-12-31T22:30:00Z", "generation": 100},
        {"startTime": "2026-01-01T01:00:00Z", "publishTime": "2025-12-31T23:30:00Z", "generation": 100},
    ]

    with pytest.raises(AccuracyDataError, match="multiple publication times"):
        calculate_accuracy(actuals, forecasts)
