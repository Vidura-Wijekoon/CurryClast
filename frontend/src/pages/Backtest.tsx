import { useState } from "react";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Legend,
} from "recharts";
import PageHeader from "../components/PageHeader";
import Metric from "../components/Metric";
import { Loading, ErrorBox } from "../components/Loading";
import { api, BacktestResponse, formatLKR } from "../lib/api";
import { itemLabel } from "../lib/items";

export default function Backtest() {
  const [holdout, setHoldout] = useState(30);
  const [data, setData] = useState<BacktestResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<unknown>(null);

  const run = async () => {
    setLoading(true);
    setError(null);
    setData(null);
    try {
      const res = await api.backtest(holdout);
      setData(res);
    } catch (e) {
      setError(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <PageHeader
        eyebrow="Insights"
        title="Backtest Savings"
        subtitle="Replay the holdout period — see exactly how much you would have saved versus gut-feel prep."
      />

      <div className="card" style={{ marginBottom: 24 }}>
        <div style={{ display: "flex", alignItems: "flex-end", gap: 24, flexWrap: "wrap" }}>
          <label className="field" style={{ minWidth: 240 }}>
            Holdout period (days)
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <input
                type="range" min={14} max={60} step={1}
                value={holdout}
                onChange={(e) => setHoldout(Number(e.target.value))}
                style={{ flex: 1 }}
              />
              <span style={{
                fontFamily: "var(--font-display)", fontSize: "1.4rem",
                color: "var(--accent)", minWidth: 50, textAlign: "right",
              }}>{holdout}</span>
            </div>
          </label>
          <button className="btn" onClick={run} disabled={loading}>
            {loading ? "Running…" : "Run backtest"}
          </button>
        </div>
      </div>

      {error && <ErrorBox error={error} />}
      {loading && <Loading label="Replaying history…" />}

      {data && (
        <>
          <div className="metric-grid">
            <Metric
              label={`LKR saved · last ${data.holdout_days} days`}
              value={formatLKR(data.savings.savings_lkr, true)}
              footnote={formatLKR(data.savings.savings_lkr)}
            />
            <Metric
              label="Naive over-prep cost"
              value={formatLKR(data.savings.naive_waste_lkr, true)}
              footnote="last-week + 30% buffer"
            />
            <Metric
              label="CurryCast over-prep cost"
              value={formatLKR(data.savings.smart_waste_lkr, true)}
              footnote="forecast + 5% buffer"
            />
          </div>

          <div className="card card-gold" style={{ marginBottom: 24 }}>
            <div className="eyebrow" style={{ color: "var(--accent)", fontSize: 11, letterSpacing: "0.2em", textTransform: "uppercase", marginBottom: 8 }}>
              The Pitch
            </div>
            <p style={{ fontFamily: "var(--font-display)", fontSize: "1.4rem", color: "var(--text)", margin: 0 }}>
              Across the last {data.holdout_days} days, CurryCast would have saved{" "}
              <span style={{ color: "var(--accent)" }}>{formatLKR(data.savings.savings_lkr)}</span>{" "}
              versus gut-feel prep — at a forecast accuracy of WAPE {(data.metrics.wape * 100).toFixed(1)}%.
            </p>
          </div>

          <h3>Forecast accuracy</h3>
          <div className="metric-grid">
            <Metric label="WAPE"          value={`${(data.metrics.wape * 100).toFixed(1)}%`} />
            <Metric label="MAPE"          value={`${(data.metrics.mape * 100).toFixed(1)}%`} />
            <Metric label="RMSE"          value={data.metrics.rmse.toFixed(2)} />
            <Metric label="Stockout rate" value={`${(data.metrics.stockout_rate * 100).toFixed(1)}%`} />
          </div>

          <div className="card card-elev">
            <h3 style={{ marginBottom: 16 }}>Actual vs. predicted · top 15 items</h3>
            <div style={{ width: "100%", height: 420 }}>
              <ResponsiveContainer>
                <BarChart
                  data={data.per_item.slice(0, 15).map((d) => ({
                    ...d,
                    label: itemLabel(d.item_canonical),
                  }))}
                  margin={{ top: 10, right: 20, left: 0, bottom: 60 }}
                >
                  <CartesianGrid strokeDasharray="2 4" stroke="rgba(212,175,55,0.10)" />
                  <XAxis
                    dataKey="label"
                    stroke="rgba(245,233,200,0.5)"
                    tick={{ fontSize: 11 }}
                    angle={-30}
                    textAnchor="end"
                    height={70}
                  />
                  <YAxis stroke="rgba(245,233,200,0.5)" tick={{ fontSize: 12 }} />
                  <Tooltip
                    contentStyle={{
                      background: "#15110a",
                      border: "1px solid rgba(212,175,55,0.4)",
                      borderRadius: 8,
                      color: "#fdf6e3",
                    }}
                  />
                  <Legend wrapperStyle={{ color: "var(--text-muted)" }} />
                  <Bar dataKey="actual"    name="Actual"    fill="#5d4435" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="predicted" name="Predicted" fill="#D4AF37" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      )}

      {!data && !loading && !error && (
        <div className="card">
          <p className="muted" style={{ margin: 0 }}>
            Pick a holdout period and click <strong style={{ color: "var(--accent)" }}>Run backtest</strong>.
          </p>
        </div>
      )}
    </>
  );
}
