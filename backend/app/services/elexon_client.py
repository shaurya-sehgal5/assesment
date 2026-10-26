from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1/datasets"
WIND_HISTORY_URL = (
    "https://data.elexon.co.uk/bmrs/api/v1/forecast/generation/wind/history"
)


class ElexonDataError(RuntimeError):
    """Raised when Elexon data cannot be retrieved or validated."""


def parse_timestamp(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError(f"Timestamp must include a timezone: {value}")
    return result.astimezone(timezone.utc)


def normalize_records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        records = payload
    elif isinstance(payload, dict):
        records = payload.get("data", payload.get("results", payload.get("value")))
    else:
        records = None

    if not isinstance(records, list):
        raise ElexonDataError(
            f"Unexpected Elexon response structure: {type(payload).__name__}"
        )
    if not all(isinstance(row, dict) for row in records):
        raise ElexonDataError("Elexon response contains a non-object record")
    return records


class ElexonClient:
    def __init__(self, timeout: float = 45.0) -> None:
        self.timeout = timeout

    def _get_json(self, url: str, params: dict[str, str]) -> Any:
        try:
            response = httpx.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise ElexonDataError(f"Elexon request failed: {exc}") from exc

    def fetch_actuals(
        self, start: datetime, end: datetime
    ) -> list[dict[str, Any]]:
        if start.tzinfo is None or end.tzinfo is None or start >= end:
            raise ValueError("Provide valid timezone-aware start and end times")

        start_utc = start.astimezone(timezone.utc)
        end_utc = end.astimezone(timezone.utc)

        # FUELHH stream filters on publication timestamps. We separately
        # filter the returned records by delivery startTime below.
        payload = self._get_json(
            f"{BASE_URL}/FUELHH/stream",
            {
                "publishDateTimeFrom": start_utc.isoformat(),
                "publishDateTimeTo": end_utc.isoformat(),
                "fuelType": "WIND",
            },
        )

        records = normalize_records(payload)
        filtered = []

        for record in records:
            if record.get("fuelType") != "WIND":
                continue
            if not isinstance(record.get("startTime"), str):
                continue
            if record.get("generation") is None:
                continue

            try:
                delivery_time = parse_timestamp(record["startTime"])
                float(record["generation"])
            except (ValueError, TypeError):
                continue

            if start_utc <= delivery_time < end_utc:
                filtered.append(record)

        filtered.sort(key=lambda row: parse_timestamp(row["startTime"]))

        if not filtered:
            raise ElexonDataError(
                "Elexon returned no WIND actuals for the requested delivery period"
            )

        return filtered

    def fetch_forecasts(
        self, start: datetime, end: datetime
    ) -> list[dict[str, Any]]:
        if start.tzinfo is None or end.tzinfo is None or start >= end:
            raise ValueError("Provide valid timezone-aware start and end times")

        start_utc = start.astimezone(timezone.utc)
        end_utc = end.astimezone(timezone.utc)

        # Request the forecast vintage before the delivery day begins.
        requested_publish_time = start_utc - timedelta(minutes=30)

        payload = self._get_json(
            WIND_HISTORY_URL,
            {"publishTime": requested_publish_time.isoformat()},
        )

        records = normalize_records(payload)
        filtered = []

        for record in records:
            if not isinstance(record.get("startTime"), str):
                continue
            if record.get("generation") is None:
                continue

            try:
                delivery_time = parse_timestamp(record["startTime"])
                float(record["generation"])
                published_at = parse_timestamp(record["publishTime"])
            except (KeyError, ValueError, TypeError):
                continue

            # Never use a forecast published at or after delivery begins.
            if published_at >= start_utc:
                continue

            if start_utc <= delivery_time < end_utc:
                filtered.append(record)

        filtered.sort(key=lambda row: parse_timestamp(row["startTime"]))

        if not filtered:
            raise ElexonDataError(
                "Elexon returned no eligible historical forecasts for this day"
            )

        # Do not silently combine forecast revisions.
        publication_times = {row["publishTime"] for row in filtered}
        if len(publication_times) != 1:
            raise ElexonDataError(
                "Multiple forecast vintages returned for the requested day"
            )

        return filtered
