from datetime import datetime, timezone

import httpx
import pytest

from app.services.elexon_client import (
    ElexonClient,
    ElexonDataError,
    normalize_records,
    parse_timestamp,
)


def test_normalize_records_accepts_array():
    records = [{"startTime": "2026-01-01T00:00:00Z"}]
    assert normalize_records(records) == records


def test_normalize_records_accepts_wrapped_data():
    records = [{"generation": 100}]
    assert normalize_records({"data": records}) == records


def test_normalize_records_rejects_unexpected_shape():
    with pytest.raises(ElexonDataError):
        normalize_records({"message": "unexpected response"})


def test_parse_timestamp_converts_to_utc():
    timestamp = parse_timestamp("2026-01-01T01:00:00+01:00")
    assert timestamp == datetime(2026, 1, 1, tzinfo=timezone.utc)


def test_fetch_actuals_filters_date_and_fuel_type(monkeypatch):
    payload = [
        {
            "startTime": "2026-01-01T00:00:00Z",
            "fuelType": "WIND",
            "generation": 100,
        },
        {
            "startTime": "2026-01-01T00:30:00Z",
            "fuelType": "GAS",
            "generation": 200,
        },
        {
            "startTime": "2026-01-02T00:00:00Z",
            "fuelType": "WIND",
            "generation": 300,
        },
    ]

    def fake_get(url, params, timeout):
        assert url.endswith("/FUELHH/stream")
        assert params["fuelType"] == "WIND"

        return httpx.Response(
            200,
            json=payload,
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(httpx, "get", fake_get)

    client = ElexonClient()
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    end = datetime(2026, 1, 2, tzinfo=timezone.utc)

    result = client.fetch_actuals(start, end)

    assert len(result) == 1
    assert result[0]["generation"] == 100


def test_fetch_rejects_invalid_range():
    client = ElexonClient()
    start = datetime(2026, 1, 2, tzinfo=timezone.utc)
    end = datetime(2026, 1, 1, tzinfo=timezone.utc)

    with pytest.raises(ValueError):
        client.fetch_actuals(start, end)
