# Windwise — UK Wind Forecast Analytics

Windwise is a React and FastAPI application for comparing UK national wind-generation forecasts with reported generation using Elexon data.

## Live application

- **Frontend:** https://heartfelt-strudel-78ff8a.netlify.app/
- **Backend health:** https://assesment-hv7z.onrender.com/health
- **Example analysis:** https://assesment-hv7z.onrender.com/api/accuracy?date=2026-01-01
- **API documentation:** https://assesment-hv7z.onrender.com/docs

## Features

- Retrieves national wind actuals from Elexon's `FUELHH` dataset, filtered to `fuelType = WIND`.
- Retrieves historical forecasts from Elexon's `WINDFOR` dataset.
- Displays forecast publication time and matched delivery hours.
- Calculates MAE, RMSE, WAPE and mean bias error.
- Visualizes hourly forecasts, actual generation and absolute errors.
- Includes automated backend tests and Docker configuration.

## Technology stack

- Frontend: React, Vite, Recharts
- Backend: Python, FastAPI, HTTPX
- Data source: Elexon BMRS API
- Tests: pytest
- Containerization: Docker, Docker Compose, Nginx
- Hosting: Netlify frontend, Render backend

## Project structure

```text
.
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   └── services/
│   │       ├── elexon_client.py
│   │       └── accuracy_service.py
│   ├── tests/
│   │   ├── test_elexon_client.py
│   │   └── test_accuracy_service.py
│   ├── requirements.txt
│   └── requirements-deploy.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   ├── index.css
│   │   └── main.jsx
│   ├── nginx.conf
│   └── package.json
├── sample_data/
│   ├── actuals-raw.json
│   └── forecasts-raw.json
├── docs/
│   └── assessment-checklist.md
├── Dockerfile.backend
├── Dockerfile.frontend
├── compose.yaml
├── .dockerignore
├── .env.example
├── .gitignore
└── README.md
```

## Run locally on Windows

### Prerequisites

- Python 3.12
- Node.js 22 or compatible and npm
- Internet access for live Elexon API requests
- Docker Desktop with Docker Compose for containerized execution

### 1. Install backend dependencies

From the repository root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

### 2. Start the backend

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

Endpoints:

- Health: http://127.0.0.1:8000/health
- API documentation: http://127.0.0.1:8000/docs
- Example analysis: http://127.0.0.1:8000/api/accuracy?date=2026-01-01

### 3. Start the frontend

Open a second PowerShell terminal:

```powershell
Set-Location .\frontend
npm ci
npm run dev
```

Open http://localhost:5173.

By default, the frontend uses `http://127.0.0.1:8000` as its API base URL. Set `VITE_API_URL` at build time to use another backend.

### 4. Run tests and build

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
Set-Location .\frontend
npm ci
npm run build
```

## Run with Docker Compose

With Docker Desktop and Docker Compose installed, run from the repository root:

```powershell
docker compose up --build
```

- Frontend: http://localhost:8080
- Backend health: http://localhost:8000/health

Stop the containers with `Ctrl+C` or run `docker compose down`. The containerized frontend uses Nginx to proxy API requests to the backend service.

## API endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Service health check |
| GET | `/api/accuracy?date=YYYY-MM-DD` | Analyze wind forecast accuracy for a UTC delivery date |

The accuracy endpoint returns source information, record counts, matched hours, aggregate metrics and hourly comparisons.

## Data and methodology

- **Actuals:** Elexon `FUELHH`, filtered to `fuelType = WIND`. Records have 30-minute resolution.
- **Forecasts:** Elexon `WINDFOR`, including delivery `startTime`, forecast `publishTime` and `generation`.
- **Aggregation:** The two half-hourly actual generation values are averaged to estimate each hourly actual value, then matched to the hourly forecast by UTC delivery-hour start time.
- **Forecast vintage:** The API reports the publication time of the selected eligible vintage returned by Elexon's API. For 1 January 2026, the currently verified vintage is `2025-12-31T22:30:00Z`.
- **Error sign:** Forecast minus actual. Positive mean bias indicates overforecasting; negative mean bias indicates underforecasting.
- **MAE:** Mean absolute error.
- **RMSE:** Root mean square error, which penalizes larger errors.
- **WAPE:** Total absolute error divided by total actual generation, expressed as a percentage.
- **Mean bias error:** Average signed forecast error.

## Limitations

The currently verified deployed example is for 1 January 2026; this alone does not establish complete evaluation coverage for every day in January. Returned forecast vintages depend on Elexon's API response and should be validated against the decision-time cutoff before operational use. The hourly actual value is the mean of two generation readings, not an energy-in-MWh calculation. Forecast error metrics alone do not quantify financial losses or savings.

## Environment variables

- `VITE_API_URL`: Frontend API base URL, set at build time. Current deployment: `https://assesment-hv7z.onrender.com`.
- `FRONTEND_ORIGIN`: Backend CORS allowlist entry. Current frontend: `https://heartfelt-strudel-78ff8a.netlify.app`.

Never commit credentials or secrets.

## AI tools disclosure

AI assistance was used for implementation guidance, debugging, test troubleshooting, documentation drafting and deployment troubleshooting. The project author is responsible for reviewing the code, validating results and ensuring the submitted implementation meets the assessment requirements.

## License

No license has been specified for this assessment project.
