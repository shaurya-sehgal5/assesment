# Windwise — UK Wind Forecast Analytics

Windwise is a React and FastAPI application for analyzing UK national wind-generation forecast accuracy using data from Elexon. It compares historical forecasts with reported generation to help users understand forecast error before making procurement decisions.

## Features

- Retrieve UK wind-generation actuals from Elexon's FUELHH dataset.
- Retrieve historical hourly wind forecasts from WINDFOR.
- Select a historical forecast vintage and compare it with actual generation.
- Calculate mean absolute error (MAE), root mean square error (RMSE), weighted absolute percentage error (WAPE), and mean bias error.
- Visualize forecast versus actual generation and absolute error by hour.
- Display data provenance, publication time, delivery date, and data resolution.

## Technology stack

- Frontend: React, Vite, Recharts
- Backend: Python, FastAPI, HTTPX
- Data source: Elexon BMRS API
- Tests: pytest
- Container configuration: Docker and Docker Compose

## Project structure

```text
.
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   └── services/
│   │       ├── accuracy_service.py
│   │       └── elexon_client.py
│   ├── requirements.txt
│   └── tests/
├── frontend/
│   ├── src/
│   ├── package.json
│   └── nginx.conf
├── sample_data/
├── docs/
├── Dockerfile.backend
├── Dockerfile.frontend
├── compose.yaml
└── README.md
```

## Requirements

- Python 3.12
- Node.js 22 or compatible
- npm
- Internet access for retrieving Elexon data
- Docker Desktop with Docker Compose, if running the containerized stack

## Run locally on Windows

### 1. Install backend dependencies

From the project root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

### 2. Start the backend

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

Backend health check:

`http://127.0.0.1:8000/health`

Interactive API documentation:

`http://127.0.0.1:8000/docs`

Example analysis:

`http://127.0.0.1:8000/api/accuracy?date=2026-01-01`

### 3. Start the frontend

In a second PowerShell terminal:

```powershell
Set-Location .\frontend
npm ci
npm run dev
```

Open `http://localhost:5173`.

For local development, the frontend uses `http://127.0.0.1:8000` by default. Set `VITE_API_URL` at build time when using a separately hosted API.

## Run tests

From the project root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Build the frontend:

```powershell
Set-Location .\frontend
npm ci
npm run build
```

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/api/accuracy?date=YYYY-MM-DD` | Analyze one UTC delivery day |

The accuracy endpoint returns the selected forecast publication time, record counts, matched hours, aggregate metrics, and hourly results.

## Methodology

- Actual generation is retrieved from FUELHH and filtered to `fuelType = WIND`.
- Actual records have 30-minute resolution; two half-hourly generation values are averaged to represent each hour.
- Forecast records from WINDFOR have hourly resolution and are matched by UTC delivery-hour start time.
- Forecast publication time is reported so users can identify the vintage used for a comparison.
- Forecast error is defined as forecast generation minus actual generation.
- MAE measures average absolute error; RMSE penalizes larger errors; WAPE expresses total absolute error relative to total actual generation.
- Mean bias error is the average signed error. Positive values indicate overforecasting; negative values indicate underforecasting.

## Data limitations

The January 1, 2026 analysis currently uses the forecast vintage published at `2025-12-31T22:30:00Z`. During investigation, the historical forecast endpoint returned the same vintage for several different requested publication times. The implementation therefore validates the publication times returned by the API rather than assuming the requested time was honored.

The selected vintage and the source data should be independently validated before using these metrics for operational procurement decisions. Historical forecast error alone does not establish financial loss or savings. The half-hourly-to-hourly aggregation is a mean of generation values, not a calculation of energy in MWh.

Raw sample responses are provided in `sample_data/` to support reproducibility. API responses and availability may change over time.

## Deployment

Docker configuration is included in `Dockerfile.backend`, `Dockerfile.frontend`, `frontend/nginx.conf`, and `compose.yaml`.

Deployment has not yet been verified. Add the final public application and API URLs here after deployment, and confirm both work in an incognito browser.

- Frontend URL: To be added
- Backend URL: To be added

## AI tools disclosure

AI assistance was used during development for implementation guidance, debugging, test troubleshooting, documentation drafting, and deployment planning. Code and outputs should be reviewed and tested by the project author before submission.

## License

Add a license if required by the assessment or intended distribution.
