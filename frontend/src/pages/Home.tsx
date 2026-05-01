import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { CalendarDays, ChefHat, CloudRain, BarChart3, MapPin, Sparkles, Users } from "lucide-react";
import { api, RestaurantInfo, getTouristSeason } from "../lib/api";

export default function Home() {
  const [r, setR] = useState<RestaurantInfo | null>(null);
  useEffect(() => { api.restaurant().then(setR).catch(() => {}); }, []);
  const isKandy = r?.city === "Kandy";
  const city = r?.city ?? "Colombo";
  const touristCtx = getTouristSeason(new Date().getMonth() + 1);

  return (
    <>
      <div className="hero">
        <div className="eyebrow" style={{ color: "var(--accent)", letterSpacing: "0.25em", fontSize: 11, textTransform: "uppercase", marginBottom: 8 }}>
          {isKandy ? "Heritage · Kandy · Asian + Sri Lankan" : "Demand & Buffet Forecasting"}
        </div>
        <h1>The kitchen, <span className="accent">prepared.</span></h1>
        <p className="muted">
          {isKandy
            ? "Tuned to the rhythms of the hill capital — Esala Perahera, Tooth Relic devotees, tea-country tourists, and Kandy's afternoon monsoon. CurryCast tells your kitchen exactly how much polos curry and lamprais to prep tomorrow."
            : "CurryCast turns your POS data, the weather, the poya calendar and Sri Lanka's tourist season into a kitchen prep list you can hand to the chef each evening."}
          {r && (
            <>
              {" "}Currently configured for <strong style={{ color: "var(--gold-200)" }}>{r.name}</strong>, {r.city}.
            </>
          )}
        </p>
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
          <Link className="btn" to="/forecast">View 7-day forecast</Link>
          <Link className="btn btn-ghost" to="/backtest">See savings</Link>
        </div>
      </div>

      <div className="metric-grid">
        <div className="metric">
          <div className="label">Cost reduction</div>
          <div className="value">3-6%</div>
          <div className="footnote">of monthly food spend</div>
        </div>
        <div className="metric">
          <div className="label">Monthly savings</div>
          <div className="value">{isKandy ? "LKR 140-280k" : "LKR 180-360k"}</div>
          <div className="footnote">{isKandy ? "Kandy heritage casual diner" : `typical mid-size ${city} restaurant`}</div>
        </div>
        <div className="metric">
          <div className="label">Payback</div>
          <div className="value">3-4 mo</div>
          <div className="footnote">after deployment</div>
        </div>
        <div className="metric">
          <div className="label">Perahera lift</div>
          <div className="value">+45%</div>
          <div className="footnote">10-day Esala spike (Kandy)</div>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: 20 }}>
        <FeatureCard icon={<CalendarDays size={28} strokeWidth={1.5} />} title="7-Day Forecast" to="/forecast"
          body="Daily covers prediction with 80% confidence band — Prophet backbone + Sri Lanka holiday + Perahera regressors." />
        <FeatureCard icon={<ChefHat size={28} strokeWidth={1.5} />} title="Tomorrow's Prep List" to="/prep"
          body={isKandy ? "Exact kg of polos curry, lamprais, kiribath. Heritage menu + Asian fusion. EN / Sinhala labels." : "Exact kg of dhal and number of fish ambul thiyal portions. EN / Sinhala labels."} />
        <FeatureCard icon={<CloudRain size={28} strokeWidth={1.5} />} title="Weather Impact" to="/weather"
          body={isKandy ? "Kandy afternoon rain - comfort food up, cold drinks down. Cool day - Ceylon tea up 10%." : "Rain on Friday - shift kottu up, cold drinks down. Heat - re-balance king coconut."} />
        <FeatureCard icon={<BarChart3 size={28} strokeWidth={1.5} />} title="Backtest Savings" to="/backtest"
          body="Replay the last 30 days. See exactly how much LKR you would have saved versus gut-feel prep." />
      </div>

      <div className="divider" />

      {/* Tourist season awareness */}
      <div className="card" style={{ marginBottom: 24, borderColor: "rgba(212,175,55,0.25)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 14 }}>
          <Users size={18} style={{ color: "var(--accent)" }} />
          <span style={{ color: "var(--accent)", letterSpacing: "0.2em", fontSize: 11, textTransform: "uppercase", fontWeight: 600 }}>
            Tourist Season · SLTDA Signal
          </span>
          <span style={{
            marginLeft: "auto",
            padding: "2px 10px",
            borderRadius: 99,
            fontSize: 12,
            fontWeight: 700,
            background: touristCtx.season === "Peak"
              ? "rgba(212,175,55,0.2)"
              : touristCtx.season === "Low"
              ? "rgba(80,60,30,0.4)"
              : "rgba(100,80,30,0.3)",
            color: touristCtx.season === "Peak" ? "var(--gold-200)" : "var(--text-muted)",
            border: "1px solid rgba(212,175,55,0.2)",
          }}>
            {touristCtx.season}
          </span>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 16 }}>
          <div>
            <div style={{ color: "var(--text-muted)", fontSize: 11, textTransform: "uppercase", letterSpacing: "0.12em", marginBottom: 4 }}>Arrival index</div>
            <div style={{ color: "var(--gold-200)", fontSize: "1.6rem", fontFamily: "var(--font-display)", fontWeight: 700 }}>
              ×{touristCtx.index.toFixed(2)}
            </div>
            <div className="muted" style={{ fontSize: 12 }}>vs. annual baseline</div>
          </div>
          <div>
            <div style={{ color: "var(--text-muted)", fontSize: 11, textTransform: "uppercase", letterSpacing: "0.12em", marginBottom: 4 }}>Cover impact</div>
            <div style={{ color: touristCtx.index >= 1 ? "var(--gold-200)" : "var(--rust)", fontSize: "1.4rem", fontFamily: "var(--font-display)", fontWeight: 700 }}>
              {touristCtx.index >= 1 ? "+" : ""}{((touristCtx.index - 1) * 100).toFixed(0)}%
            </div>
            <div className="muted" style={{ fontSize: 12 }}>tourist-driven covers</div>
          </div>
          <div style={{ gridColumn: "span 2" }}>
            <div style={{ color: "var(--text-muted)", fontSize: 11, textTransform: "uppercase", letterSpacing: "0.12em", marginBottom: 4 }}>Seasonal note</div>
            <div className="muted" style={{ fontSize: 13, lineHeight: 1.55 }}>{touristCtx.note}</div>
          </div>
          {touristCtx.upcoming && (
            <div style={{ gridColumn: "span 2" }}>
              <div style={{ color: "var(--text-muted)", fontSize: 11, textTransform: "uppercase", letterSpacing: "0.12em", marginBottom: 4 }}>Coming up</div>
              <div className="muted" style={{ fontSize: 13 }}>{touristCtx.upcoming}</div>
            </div>
          )}
        </div>
      </div>

      {isKandy && (
        <div className="card card-gold" style={{ marginBottom: 24 }}>
          <div className="eyebrow" style={{ color: "var(--accent)", letterSpacing: "0.2em", fontSize: 11, textTransform: "uppercase", marginBottom: 12 }}>
            <Sparkles size={14} style={{ display: "inline", marginRight: 6, verticalAlign: "-2px" }} />
            Tuned for Kandy
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 18, marginTop: 8 }}>
            <KandyFact title="Esala Perahera" body="10-day procession in July/August — 45% covers lift, weekend nights up to 65%." />
            <KandyFact title="Tooth Relic devotees" body="Daily pilgrim flow lifts lunch covers ~5%; +25% on poya." />
            <KandyFact title="Hill-country weather" body="Cooler than Colombo (avg 23-26°C). Afternoon rain May-Sept and Oct-Dec." />
            <KandyFact title="Heritage menu" body="Polos curry, lamprais, kiribath, watalappan — all weighted with Kandy-specific ratios." />
          </div>
        </div>
      )}

      <div className="card card-gold">
        <div className="eyebrow" style={{ color: "var(--accent)", letterSpacing: "0.2em", fontSize: 11, textTransform: "uppercase", marginBottom: 8 }}>
          <MapPin size={14} style={{ display: "inline", marginRight: 6, verticalAlign: "-2px" }} />
          The Pitch
        </div>
        <p style={{ fontFamily: "var(--font-display)", fontSize: "1.3rem", color: "var(--text)", margin: 0 }}>
          {isKandy
            ? "Some Perahera Saturdays we cook for 200 covers and 80 walk in - the rest goes to the staff or the bin. Other Saturdays we run out of polos curry by 8 PM. We just guess."
            : "Some Saturdays we cook for 200 covers and 80 walk in - the rest goes to the staff or the bin. Other Saturdays we run out of pol sambol by 8 PM and lose half the rice-and-curry crowd. We just guess."}
        </p>
        <p className="dim" style={{ marginTop: 16 }}>
          - Restaurant owner, {city}. CurryCast turns that guess into a forecast.
        </p>
      </div>
    </>
  );
}

function FeatureCard({ icon, title, body, to }: { icon: React.ReactNode; title: string; body: string; to: string }) {
  return (
    <Link to={to} className="card" style={{ textDecoration: "none", color: "inherit", display: "block" }}>
      <div style={{ color: "var(--accent)", marginBottom: 12 }}>{icon}</div>
      <h3 style={{ marginBottom: 8 }}>{title}</h3>
      <p style={{ marginBottom: 0 }}>{body}</p>
    </Link>
  );
}

function KandyFact({ title, body }: { title: string; body: string }) {
  return (
    <div>
      <div style={{ color: "var(--gold-200)", fontWeight: 600, marginBottom: 4, fontSize: 14 }}>{title}</div>
      <div className="muted" style={{ fontSize: 13 }}>{body}</div>
    </div>
  );
}
