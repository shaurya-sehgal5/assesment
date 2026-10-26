from datetime import datetime, timedelta, timezone

import httpx


BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"
ACTUALS_URL = f"{BASE_URL}/datasets/FUELHH/stream"
FORECASTS_URL = f"{BASE_URL}/datasets/WINDFOR"


class ElexonDataError(Exception):
    """Raised when Elexon data cannot be retrieved or validated."""


def parse_timestamp(value):
    if not value:
        raise ElexonDataError("Missing timestamp in Elexon response.")

    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def normalize_records(payload):
    if isinstance(payload, list):
        return payload

    if isinstance(payload, dict):
        for key in ("data", "results", "value"):
            if isinstance(payload.get(key), list):
                return payload[key]

    raise ElexonDataError("Unexpected response format from Elexon.")


class ElexonClient:
    def _get_json(self, url, params):
        try:
            response = httpx.get(url, params=params, timeout=60.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            raise ElexonDataError(f"Elexon request failed: {exc}") from exc
        except ValueError as exc:
            raise ElexonDataError("Elexon returned invalid JSON.") from exc

    def fetch_actuals(self, start, end):
        start = parse_timestamp(start.isoformat())
        end = parse_timestamp(end.isoformat())

        if start >= end:
            raise ValueError("Invalid date range: start must be before end.")

        payload = self._get_json(
            ACTUALS_URL,
            {
                "publishDateTimeFrom": (start - timedelta(hours=2)).isoformat(),
                "publishDateTimeTo": (end + timedelta(hours=1)).isoformat(),
                "fuelType": "WIND",
            },
        )

        records = normalize_records(payload)
        actuals = []

        for record in records:
            if record.get("fuelType") != "WIND":
                continue

            delivery_time = parse_timestamp(record["startTime"])

            if start <= delivery_time < end:
                actuals.append(record)

        actuals.sort(key=lambda row: row["startTime"])

        if not actuals:
            raise ElexonDataError("No wind actuals found for the requested period.")

        return actuals

    def fetch_forecasts(self, start, end):
        start = parse_timestamp(start.isoformat())
        end = parse_timestamp(end.isoformat())

        # Retrieve vintages published during the 24 hours before delivery starts.
        payload = self._get_json(
            FORECASTS_URL,
            {
                "publishDateTimeFrom": (start - timedelta(hours=24)).isoformat(),
                "publishDateTimeTo": start.isoformat(),
            },
        )

        records = normalize_records(payload)

        # Trust the publication timestamps in the returned records, not just
        # the endpoint's requested publication-time range.
        eligible = []

        for record in records:
            if not record.get("publishTime") or not record.get("startTime"):
                continue

            published = parse_timestamp(record["publishTime"])
            delivery = parse_timestamp(record["startTime"])

            if published <= start and start <= delivery < end:
                eligible.append(record)

        if not eligible:
            raise ElexonDataError(
                "No pre-delivery wind forecast vintage found for the requested period."
            )

        selected_publish_time = max(
            parse_timestamp(record["publishTime"]) for record in eligible
        )

        forecasts = [
            record for record in eligible
            if parse_timestamp(record["publishTime"]) == selected_publish_time
        ]

        forecasts.sort(key=lambda row: row["startTime"])

        if len(forecasts) != 24:
            raise ElexonDataError(
                f"Expected 24 hourly forecasts, found {len(forecasts)} "
                f"for vintage {selected_publish_time.isoformat()}."
            )

        if any(record.get("generation") is None for record in forecasts):
            raise ElexonDataError("Selected forecast vintage contains missing generation.")

        return forecasts
