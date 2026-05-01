import { useEffect, useMemo, useState } from "react";
import PageHeader from "../components/PageHeader";
import { Loading, ErrorBox } from "../components/Loading";
import { api, PredictResponse, formatDate } from "../lib/api";
import { ITEM_LABELS, itemIcon } from "../lib/items";

export default function PrepList() {
  const [data, setData] = useState<PredictResponse | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [selectedDate, setSelectedDate] = useState<string>("");

  useEffect(() => {
    api.predict(7).then((d) => {
      setData(d);
      if (d.prep_list.length > 0) {
        const dates = [...new Set(d.prep_list.map((p) => p.date))].sort();
        setSelectedDate(dates[0]);
      }
    }).catch(setError);
  }, []);

  const dates = useMemo(() => {
    if (!data) return [];
    return [...new Set(data.prep_list.map((p) => p.date))].sort();
  }, [data]);

  const todayPrep = useMemo(() => {
    if (!data || !selectedDate) return [];
    return data.prep_list
      .filter((p) => p.date === selectedDate)
      .sort((a, b) => b.prep_qty - a.prep_qty);
  }, [data, selectedDate]);

  const expectedCovers = useMemo(() => {
    if (!data || !selectedDate) return 0;
    const f = data.daily_forecast.find((d) => d.date === selectedDate);
    return f ? Math.round(f.yhat) : 0;
  }, [data, selectedDate]);

  if (error) return <ErrorBox error={error} />;
  if (!data) return <Loading label="Loading prep list…" />;

  const exportCSV = () => {
    const rows = [["Item", "Quantity", "Unit"]];
    todayPrep.forEach((p) => {
      const label = ITEM_LABELS[p.item_canonical]?.en ?? p.item_canonical;
      rows.push([label, String(p.prep_qty), p.unit]);
    });
    const csv = rows.map((r) => r.map((c) => `"${c}"`).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `prep_${selectedDate}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <>
      <PageHeader
        eyebrow="Operations"
        title="Tomorrow's Prep List"
        subtitle="Hand this to the chef tonight at 10 PM. Quantities include a 5% buffer."
        right={
          <button className="btn btn-ghost" onClick={exportCSV}>Export CSV</button>
        }
      />

      <div style={{ display: "flex", alignItems: "flex-end", gap: 24, flexWrap: "wrap", marginBottom: 24 }}>
        <label className="field" style={{ minWidth: 280 }}>
          Pick a day
          <select className="select" value={selectedDate} onChange={(e) => setSelectedDate(e.target.value)}>
            {dates.map((d) => (
              <option key={d} value={d}>{formatDate(d)}</option>
            ))}
          </select>
        </label>

        <div className="metric" style={{ minWidth: 220 }}>
          <div className="label">Expected covers</div>
          <div className="value">{expectedCovers}</div>
          <div className="footnote">includes confidence buffer</div>
        </div>
      </div>

      <div className="prep-grid">
        {todayPrep.map((p) => {
          const label = ITEM_LABELS[p.item_canonical];
          return (
            <div key={p.item_canonical} className="prep-card">
              <div className="icon">{itemIcon(p.item_canonical)}</div>
              <div className="name">{label?.en ?? p.item_canonical}</div>
              {(label?.si || label?.ta) && (
                <div className="dim" style={{ fontSize: 12, marginBottom: 8 }}>
                  {label?.si} {label?.si && label?.ta && "·"} {label?.ta}
                </div>
              )}
              <div className="qty">{p.prep_qty.toFixed(1)}</div>
              <div className="unit">{p.unit}</div>
            </div>
          );
        })}
      </div>

      <div className="divider" />

      <div className="card">
        <h3 style={{ marginBottom: 12 }}>Print-friendly table</h3>
        <table className="table">
          <thead>
            <tr>
              <th>Item</th>
              <th style={{ textAlign: "right" }}>Quantity</th>
              <th>Unit</th>
            </tr>
          </thead>
          <tbody>
            {todayPrep.map((p) => (
              <tr key={p.item_canonical}>
                <td>
                  <span style={{ marginRight: 8 }}>{itemIcon(p.item_canonical)}</span>
                  {ITEM_LABELS[p.item_canonical]?.en ?? p.item_canonical}
                </td>
                <td className="num">{p.prep_qty.toFixed(1)}</td>
                <td className="muted">{p.unit}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
