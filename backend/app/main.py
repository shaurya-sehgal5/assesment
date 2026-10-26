import os
from datetime import datetime, time, timedelta, timezone

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.services.accuracy_service import AccuracyDataError, calculate_accuracy
from app.services.elexon_client import ElexonClient, ElexonDataError

app = FastAPI(
    title="Energy Forecast Analytics API",
    description=(
        "UK wind generation forecast accuracy for electricity "
        "procurement analysis, using Elexon data."
    ),
    version="0.2.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://heartfelt-strudel-78ff8a.netlify.app",
        *[
            origin.strip().rstrip("/")
            for origin in os.getenv("FRONTEND_ORIGIN", "").split(",")
            if origin.strip()
        ],
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


client = ElexonClient()


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "energy-forecast-api",
        "version": "0.2.0",
    }


@app.get("/api/accuracy")
def get_accuracy(
    date: str = Query(
        ...,
        description="UTC delivery date in YYYY-MM-DD format",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    ),
):
    try:
        delivery_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date. Use YYYY-MM-DD, for example 2026-01-01.",
        )

    start = datetime.combine(
        delivery_date, time.min, tzinfo=timezone.utc
    )
    end = start + timedelta(days=1)

    try:
        actuals = client.fetch_actuals(start, end)
        forecasts = client.fetch_forecasts(start, end)
        result = calculate_accuracy(actuals, forecasts)

        return {
            "date": date,
            "timezone": "UTC",
            "actualRecords": len(actuals),
            "forecastRecords": len(forecasts),
            "actualResolution": "30 minutes",
            "forecastResolution": "1 hour",
            "aggregation": "Mean of the two half-hourly actuals per hour",
            **result,
        }

    except (ElexonDataError, AccuracyDataError) as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
