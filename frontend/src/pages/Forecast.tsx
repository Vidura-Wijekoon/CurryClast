import { useEffect, useState } from "react";
import {
  ResponsiveContainer, ComposedChart, Line, Area,
  XAxis, YAxis, Tooltip, CartesianGrid,
} from "recharts";
import PageHeader from "../components/PageHeader";
import Metric from "../components/Metric";
import { Loading, ErrorBox } from "../components/Loading";
import { api, PredictResponse, formatDate, getTouristSeason } from "../lib/api";

export default function Forecast() {
  const [data, setData] = useState<PredictResponse | null>(null);
  const [error, setError] = useState<unknown>(null);

  useEffect(() => {
    api.predict(7).then(setData).catch(setError);
  }, []);

  if (error) return <ErrorBox error={error} />;
  if (!data) return <Loading label="Computing forecast…" />;

  const daily = data.daily_forecast.map((d) => ({
    ...d,
    label: formatDate(d.date, "short"),
    yhat: Math.round(d.yhat),
    yhat_lower: Math.round(d.yhat_lower),
    yhat_upper: Math.round(d.yhat_upper),
  }));

  const avg = Math.round(daily.reduce((a, b) => a + b.yhat, 0) / daily.length);
  const peak = daily.reduce((a, b) => (b.yhat > a.yhat ? b : a));
  const low = daily.reduce((a, b) => (b.yhat < a.yhat ? b : a));
  const touristCtx = getTouristSeason(new Date().getMonth() + 1);

  return (
    <>
      <PageHeader
        eyebrow="Operations"
        title="Seven-Day Forecast"
        subtitle="Daily covers with 80% confidence interval. Prophet backbone, Sri Lanka holiday + tourist season regressors."
      />

      <div style={{
        display: "flex", alignItems: "center", gap: 10, marginBottom: 20,
        padding: "10px 16px", borderRadius: 8,
        background: "rgba(212,175,55,0.06)", border: "1px solid rgba(212,175,55,0.18)",
      }}>
        <span style={{ fontSize: 12, color: "var(--text-muted)" }}>Tourist season:</span>
        <span style={{
          padding: "2px 9px", borderRadius: 99, fontSize: 12, fontWeight: 700,
          background: touristCtx.season === "Peak" ? "rgba(212,175,55,0.2)" : touristCtx.season === "Low" ? "rgba(80,60,30,0.4)" : "rgba(100,80,30,0.3)",
          color: touristCtx.season === "Peak" ? "var(--gold-200)" : "var(--text-muted)",
          border: "1px solid rgba(212,175,55,0.2)",
        }}>{touristCtx.season}</span>
        <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
          Arrival index <strong style={{ color: touristCtx.index >= 1 ? "var(--gold-200)" : "var(--rust)" }}>×{touristCtx.index.toFixed(2)}</strong>
          <span className="dim"> · {touristCtx.index >= 1 ? "+" : ""}{((touristCtx.index - 1) * 100).toFixed(0)}% tourist-driven covers baked into forecast</span>
        </span>
      </div>

      <div className="metric-grid">
        <Metric label="Average covers / day" value={avg} footnote="next 7 days" />
        <Metric label="Peak day" value={peak.label} footnote={`${peak.yhat} covers`} />
        <Metric label="Lowest day" value={low.label} footnote={`${low.yhat} covers`} />
        <Metric label="Forecast horizon" value="7 days" footnote="hourly granularity available" />
      </div>

      <div className="card card-elev" style={{ marginBottom: 24 }}>
        <h3 style={{ marginBottom: 16 }}>Daily covers · forecast vs. interval</h3>
        <div style={{ width: "100%", height: 380 }}>
          <ResponsiveContainer>
            <ComposedChart data={daily} margin={{ top: 10, right: 30, left: 0, bottom: 10 }}>
              <defs>
                <linearGradient id="goldArea" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%"  stopColor="#D4AF37" stopOpacity={0.32} />
                  <stop offset="100%" stopColor="#D4AF37" stopOpacity={0.04} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="2 4" stroke="rgba(212,175,55,0.12)" />
              <XAxis dataKey="label" stroke="rgba(245,233,200,0.5)" tick={{ fontSize: 12 }} />
              <YAxis stroke="rgba(245,233,200,0.5)" tick={{ fontSize: 12 }} />
              <Tooltip
                contentStyle={{
                  background: "#15110a",
                  border: "1px solid rgba(212,175,55,0.4)",
                  borderRadius: 8,
                  color: "#fdf6e3",
                }}
              />
              <Area type="monotone" dataKey="yhat_upper" stroke="none" fill="url(#goldArea)" />
              <Area type="monotone" dataKey="yhat_lower" stroke="none" fill="#15110a" />
              <Line
                type="monotone" dataKey="yhat"
                stroke="#D4AF37" strokeWidth={3}
                dot={{ fill: "#D4AF37", r: 5, strokeWidth: 2, stroke: "#0a0805" }}
                activeDot={{ r: 7 }}
                name="Forecast covers"
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="card">
        <h3 style={{ marginBottom: 16 }}>Daily numbers</h3>
        <table className="table">
          <thead>
            <tr>
              <th>Date</th>
              <th style={{ textAlign: "right" }}>Forecast</th>
              <th style={{ textAlign: "right" }}>Lower (80%)</th>
              <th style={{ textAlign: "right" }}>Upper (80%)</th>
            </tr>
          </thead>
          <tbody>
            {daily.map((d) => (
              <tr key={d.date}>
                <td>{formatDate(d.date)}</td>
                <td className="num">{d.yhat}</td>
                <td className="num" style={{ color: "var(--text-muted)" }}>{d.yhat_lower}</td>
                <td className="num" style={{ color: "var(--text-muted)" }}>{d.yhat_upper}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
