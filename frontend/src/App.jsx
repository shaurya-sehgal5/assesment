import { useEffect, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  BarChart,
  Bar,
} from "recharts";
import "./App.css";

const API = import.meta.env.VITE_API_URL || "";

function formatNumber(value) {
  return Number(value).toLocaleString("en-GB", {
    maximumFractionDigits: 1,
  });
}

function formatTime(value) {
  return new Date(value).toLocaleTimeString("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "UTC",
    timeZoneName: undefined,
  });
}

function MetricCard({ label, value, detail }) {
  return (
    <article className="metric-card">
      <p className="metric-label">{label}</p>
      <div className="metric-value">{value}</div>
      <p className="metric-detail">{detail}</p>
    </article>
  );
}

export default function App() {
  const [date, setDate] = useState("2026-01-01");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function loadData(selectedDate) {
    setLoading(true);
    setError("");
    setData(null);

    try {
      const response = await fetch(
        `${API}/api/accuracy?date=${encodeURIComponent(selectedDate)}`
      );
      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || "Unable to load forecast accuracy.");
      }

      setData(result);
    } catch (err) {
      setError(
        `${err.message}. Confirm the FastAPI backend is running on port 8000.`
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData(date);
  }, []);

  const chartData = (data?.hourlyResults ?? []).map((row) => ({
    ...row,
    time: formatTime(row.startTime),
  }));

  return (
    <main className="app-shell">
      <header className="topbar">
        <a className="brand" href="#overview">
          <span className="brand-mark">W</span>
          <span>Windwise</span>
        </a>
        <span className="source-pill">
          <span className="status-dot" />
          Elexon data
        </span>
      </header>

      <section className="hero" id="overview">
        <div>
          <p className="eyebrow">ENERGY INTELLIGENCE / WIND</p>
          <h1>Forecast performance</h1>
          <p className="hero-copy">
            Understand forecast error before it becomes a procurement problem.
            Compare expected and actual UK wind generation.
          </p>
        </div>

        <form
          className="date-form"
          onSubmit={(event) => {
            event.preventDefault();
            loadData(date);
          }}
        >
          <label htmlFor="delivery-date">Delivery date (UTC)</label>
          <div className="date-controls">
            <input
              id="delivery-date"
              type="date"
              value={date}
              onChange={(event) => setDate(event.target.value)}
              required
            />
            <button type="submit" disabled={loading}>
              {loading ? "Loading…" : "Analyze"}
            </button>
          </div>
        </form>
      </section>

      {loading && (
        <div className="message-panel" role="status">
          Retrieving actuals and historical forecasts from Elexon…
        </div>
      )}

      {error && (
        <div className="message-panel error-panel" role="alert">
          <strong>Unable to load analytics</strong>
          <p>{error}</p>
          <button onClick={() => loadData(date)}>Try again</button>
        </div>
      )}

      {data && !loading && (
        <>
          <section className="metrics-grid">
            <MetricCard
              label="Mean absolute error"
              value={`${formatNumber(data.mae)} MW`}
              detail="Average absolute difference"
            />
            <MetricCard
              label="Root mean square error"
              value={`${formatNumber(data.rmse)} MW`}
              detail="Penalizes larger errors"
            />
            <MetricCard
              label="Weighted absolute error"
              value={`${formatNumber(data.wapePercent)}%`}
              detail="Absolute error / total actual"
            />
            <MetricCard
              label="Matched delivery hours"
              value={`${data.matchedHours} / 24`}
              detail={`${data.actualRecords} actual records · ${data.forecastRecords} forecasts`}
            />
          </section>

          <section className="panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">GENERATION PROFILE</p>
                <h2>Forecast vs actual</h2>
              </div>
              <span className="unit-label">Generation (MW)</span>
            </div>
            <div className="chart-container">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 12, right: 16, left: 4, bottom: 4 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e7eaf0" />
                  <XAxis dataKey="time" tick={{ fontSize: 11 }} minTickGap={24} />
                  <YAxis
                    tick={{ fontSize: 11 }}
                    width={70}
                    tickFormatter={(value) => `${Math.round(value / 1000)}k`}
                  />
                  <Tooltip
                    formatter={(value) => [`${formatNumber(value)} MW`]}
                    labelFormatter={(label) => `${label} UTC`}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="actual"
                    name="Actual"
                    stroke="#147d64"
                    strokeWidth={2.5}
                    dot={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="forecast"
                    name="Forecast"
                    stroke="#5268d8"
                    strokeWidth={2.5}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </section>

          <section className="panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">ERROR ANALYSIS</p>
                <h2>Absolute error by hour</h2>
              </div>
              <span className="unit-label">MW</span>
            </div>
            <div className="chart-container short-chart">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 12, right: 16, left: 4, bottom: 4 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e7eaf0" />
                  <XAxis dataKey="time" tick={{ fontSize: 11 }} minTickGap={24} />
                  <YAxis tick={{ fontSize: 11 }} width={70} />
                  <Tooltip
                    formatter={(value) => [`${formatNumber(value)} MW`]}
                    labelFormatter={(label) => `${label} UTC`}
                  />
                  <Bar
                    dataKey="absoluteError"
                    name="Absolute error"
                    fill="#e5a34d"
                    radius={[4, 4, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </section>

          <section className="panel data-panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">DATA PROVENANCE</p>
                <h2>Analysis details</h2>
              </div>
            </div>
            <dl className="details-grid">
              <div>
                <dt>Delivery date</dt>
                <dd>{data.date} (UTC)</dd>
              </div>
              <div>
                <dt>Forecast published</dt>
                <dd>{data.forecastPublishTime}</dd>
              </div>
              <div>
                <dt>Actual resolution</dt>
                <dd>{data.actualResolution}</dd>
              </div>
              <div>
                <dt>Forecast resolution</dt>
                <dd>{data.forecastResolution}</dd>
              </div>
              <div className="wide-detail">
                <dt>Aggregation method</dt>
                <dd>{data.aggregation}</dd>
              </div>
            </dl>
            <p className="disclaimer">
              Historical analysis only. Forecast-vintage selection and source
              data must be validated before using these metrics for procurement
              decisions. Forecast error is not itself a measure of financial loss.
            </p>
          </section>
        </>
      )}

      <footer>
        <span>Windwise · Wind generation analytics</span>
        <span>Times shown in UTC · Data source: Elexon</span>
      </footer>
    </main>
  );
}

