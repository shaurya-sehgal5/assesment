from collections import defaultdict
from datetime import datetime, timezone
from math import sqrt
from typing import Any


class AccuracyDataError(ValueError):
    """Raised when actuals and forecasts cannot be compared reliably."""


def _timestamp(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise AccuracyDataError(f"Timestamp must include timezone: {value}")
    return result.astimezone(timezone.utc)


def _generation(record: dict[str, Any]) -> float:
    value = record.get("generation")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AccuracyDataError("Generation must be a numeric value")
    return float(value)


def calculate_accuracy(
    actuals: list[dict[str, Any]],
    forecasts: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compare half-hourly FUELHH actuals with hourly WINDFOR forecasts.

    Each actual's startTime labels its half-hour interval. Two half-hour
    values are averaged to represent each hour. Forecasts are matched by
    the start of that hour. All timestamps are normalized to UTC.
    """
    if not actuals or not forecasts:
        raise AccuracyDataError("Actuals and forecasts must both be non-empty")

    actual_by_hour: dict[datetime, list[float]] = defaultdict(list)
    for row in actuals:
        if row.get("fuelType") != "WIND":
            continue

        timestamp = _timestamp(row["startTime"])
        hour = timestamp.replace(minute=0, second=0, microsecond=0)
        actual_by_hour[hour].append(_generation(row))

    hourly_actuals: dict[datetime, float] = {}
    for hour, values in actual_by_hour.items():
        if len(values) != 2:
            raise AccuracyDataError(
                f"Expected 2 half-hour actuals for {hour.isoformat()}, "
                f"found {len(values)}"
            )
        hourly_actuals[hour] = sum(values) / len(values)

    forecast_by_hour: dict[datetime, float] = {}
    publication_times = set()

    for row in forecasts:
        timestamp = _timestamp(row["startTime"])
        if timestamp.minute != 0 or timestamp.second != 0:
            raise AccuracyDataError(
                f"Forecast timestamp is not hourly: {row['startTime']}"
            )
        if timestamp in forecast_by_hour:
            raise AccuracyDataError(
                f"Duplicate forecast for {timestamp.isoformat()}"
            )
        forecast_by_hour[timestamp] = _generation(row)

        publish_time = row.get("publishTime")
        if publish_time:
            publication_times.add(_timestamp(publish_time))

    if len(publication_times) > 1:
        raise AccuracyDataError(
            "Forecasts contain multiple publication times; "
            "select one forecast vintage before evaluating accuracy"
        )

    common_hours = sorted(set(hourly_actuals) & set(forecast_by_hour))
    if not common_hours:
        raise AccuracyDataError("No matching hourly actuals and forecasts")

    rows = []
    for hour in common_hours:
        actual = hourly_actuals[hour]
        forecast = forecast_by_hour[hour]
        error = forecast - actual
        rows.append({
            "startTime": hour.isoformat().replace("+00:00", "Z"),
            "actual": round(actual, 3),
            "forecast": round(forecast, 3),
            "error": round(error, 3),
            "absoluteError": round(abs(error), 3),
        })

    errors = [row["forecast"] - row["actual"] for row in rows]
    absolute_errors = [abs(error) for error in errors]
    actual_total = sum(row["actual"] for row in rows)

    mean_bias = sum(errors) / len(errors)

    return {
        "forecastPublishTime": (
            next(iter(publication_times)).isoformat().replace("+00:00", "Z")
            if publication_times else None
        ),
        "matchedHours": len(rows),
        "mae": round(sum(absolute_errors) / len(rows), 3),
        "rmse": round(sqrt(sum(error ** 2 for error in errors) / len(rows)), 3),
        "wapePercent": (
            round(sum(absolute_errors) / actual_total * 100, 3)
            if actual_total else None
        ),
        "meanBiasError": round(mean_bias, 3),
        "biasDirection": (
            "overforecast" if mean_bias > 0
            else "underforecast" if mean_bias < 0
            else "unbiased on average"
        ),
        "hourlyResults": rows,
    }
