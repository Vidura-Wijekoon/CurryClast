import { useEffect, useMemo, useState } from "react";
import { TrendingUp, TrendingDown } from "lucide-react";
import PageHeader from "../components/PageHeader";
import { Loading, ErrorBox } from "../components/Loading";
import { api, PredictResponse, formatDate } from "../lib/api";
import { itemLabel } from "../lib/items";

const COMFORT = new Set(["chicken_kottu", "string_hoppers", "egg_kottu", "cheese_kottu"]);
const COLD_DRINKS = new Set(["king_coconut", "faluda"]);
const SHRINKAGE = 1.05;

// Default consumption ratios (kg/cover) — match buffet_translator.yaml defaults.
const RATIOS: Record<string, number> = {
  rice: 0.20, dhal_curry: 0.11, pol_sambol: 0.045,
  fish_ambul_thiyal: 0.075, chicken_curry: 0.13,
  chicken_kottu: 0.28, cheese_kottu: 0.18, egg_kottu: 0.20,
  string_hoppers: 0.17, egg_hopper: 0.05, devilled_chicken: 0.085,
  cashew_curry: 0.055, brinjal_moju: 0.055, seer_fish_curry: 0.07,
  king_coconut: 0.5, lion_lager: 0.4, faluda: 0.25,
};

function weatherIcon(rain_mm: number) {
  if (rain_mm > 5) return "🌧️";
  if (rain_mm > 1) return "🌦️";
  return "☀️";
}

export default function WeatherImpact() {
  const [data, setData] = useState<PredictResponse | null>(null);
  const [error, setError] = useState<unknown>(null);

  useEffect(() => {
    api.predict(7).then(setData).catch(setError);
  }, []);

  const adjustments = useMemo(() => {
    if (!data) return [];
    const rows: { date: string; item: string; baseQty: number; adjQty: number; delta: number; pct: number; unit: string }[] = [];
    for (const day of data.weather) {
      const fc = data.daily_forecast.find((f) => f.date === day.date);
      if (!fc) continue;
      const covers = fc.yhat;
      for (const item of Object.keys(RATIOS)) {
        const base = covers * RATIOS[item] * SHRINKAGE;
        let adj = base;
        if (day.rain_mm > 5 && COMFORT.has(item)) adj *= 1.12;
        if (day.rain_mm > 5 && COLD_DRINKS.has(item)) adj *= 0.6;
        if (day.temp_c > 33 && item === "king_coconut") adj *= 1.10;
        if (day.temp_c > 33 && item === "rice") adj *= 0.92;

        const prepRow = data.prep_list.find((p) => p.date === day.date && p.item_canonical === item);
        const unit = prepRow?.unit ?? "kg";
        const delta = adj - base;
        if (Math.abs(delta) > 0.01) {
          rows.push({
            date: day.date,
            item,
            baseQty: base,
            adjQty: adj,
            delta,
            pct: (delta / base) * 100,
            unit,
          });
        }
      }
    }
    return rows.sort((a, b) => Math.abs(b.pct) - Math.abs(a.pct));
  }, [data]);

  if (error) return <ErrorBox error={error} />;
  if (!data) return <Loading label="Loading weather forecast…" />;

  const major = adjustments.filter((a) => Math.abs(a.pct) >= 4).slice(0, 10);

  return (
    <>
      <PageHeader
        eyebrow="Operations"
        title="Weather Impact"
        subtitle="How tomorrow's weather is reshaping the prep list."
      />

      <h3>7-day weather outlook · {data.city}</h3>
      <div className="weather-strip">
        {data.weather.map((w) => (
          <div key={w.date} className="weather-day">
            <div className="day">{formatDate(w.date, "short").split(" ")[0]}</div>
            <div className="icon">{weatherIcon(w.rain_mm)}</div>
            <div className="temp">{w.temp_c.toFixed(1)}°C</div>
            <div className="rain">Rain: {w.rain_mm.toFixed(1)} mm</div>
          </div>
        ))}
      </div>

      <h3>📣 Today's adjustments</h3>
      {major.length === 0 ? (
        <div className="card">
          <p className="muted" style={{ margin: 0 }}>Mild weather ahead — no major prep changes recommended.</p>
        </div>
      ) : (
        <div>
          {major.map((a, i) => (
            <div key={i} className={`adj-row ${a.delta < 0 ? "down" : ""}`}>
              <div>
                <strong style={{ color: "var(--text)" }}>{formatDate(a.date, "short").split(" ")[0]}</strong>
                <span className="dim" style={{ margin: "0 8px" }}>·</span>
                <em className="muted">{itemLabel(a.item)}</em>
              </div>
              <div className="delta" style={{ color: a.delta > 0 ? "var(--gold-200)" : "var(--rust)", display: "flex", alignItems: "center", gap: 8 }}>
                {a.delta > 0 ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                {a.delta > 0 ? "+" : ""}{a.delta.toFixed(1)} {a.unit}
                <span className="dim" style={{ fontWeight: 400, fontSize: 12 }}>({a.pct >= 0 ? "+" : ""}{a.pct.toFixed(0)}%)</span>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="divider" />

      <h3>Full comparison</h3>
      <div className="card" style={{ padding: 0, overflow: "hidden" }}>
        <table className="table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Item</th>
              <th style={{ textAlign: "right" }}>Baseline</th>
              <th style={{ textAlign: "right" }}>Weather-adj.</th>
              <th>Unit</th>
              <th style={{ textAlign: "right" }}>Δ</th>
              <th style={{ textAlign: "right" }}>Δ %</th>
            </tr>
          </thead>
          <tbody>
            {adjustments.map((a, i) => (
              <tr key={i}>
                <td>{formatDate(a.date, "short")}</td>
                <td>{itemLabel(a.item)}</td>
                <td className="num" style={{ color: "var(--text-muted)" }}>{a.baseQty.toFixed(1)}</td>
                <td className="num">{a.adjQty.toFixed(1)}</td>
                <td className="muted">{a.unit}</td>
                <td className="num" style={{ color: a.delta > 0 ? "var(--gold-200)" : "var(--rust)" }}>
                  {a.delta > 0 ? "+" : ""}{a.delta.toFixed(1)}
                </td>
                <td className="num" style={{ color: a.delta > 0 ? "var(--gold-200)" : "var(--rust)" }}>
                  {a.pct >= 0 ? "+" : ""}{a.pct.toFixed(0)}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
