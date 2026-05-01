import { NavLink } from "react-router-dom";
import { Home, CalendarDays, ChefHat, CloudRain, BarChart3 } from "lucide-react";

const links = [
  { to: "/",          label: "Overview",         icon: Home,         section: "Main" },
  { to: "/forecast",  label: "7-Day Forecast",   icon: CalendarDays, section: "Operations" },
  { to: "/prep",      label: "Tomorrow's Prep",  icon: ChefHat,      section: "Operations" },
  { to: "/weather",   label: "Weather Impact",   icon: CloudRain,    section: "Operations" },
  { to: "/backtest",  label: "Backtest Savings", icon: BarChart3,    section: "Insights" },
];

export default function Sidebar() {
  const grouped = links.reduce<Record<string, typeof links>>((acc, l) => {
    (acc[l.section] ||= []).push(l);
    return acc;
  }, {});

  return (
    <aside className="sidebar">
      <div className="logo">
        <div className="logo-mark">K</div>
        <div>
          <div className="logo-name">Kulture32</div>
          <div className="logo-sub">Kandy · Heritage</div>
        </div>
      </div>

      {Object.entries(grouped).map(([section, items]) => (
        <div key={section}>
          <div className="nav-section-title">{section}</div>
          {items.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}
            >
              <Icon strokeWidth={1.7} />
              <span>{label}</span>
            </NavLink>
          ))}
        </div>
      ))}

      <div style={{ marginTop: 32, fontSize: 11, color: "var(--text-dim)", letterSpacing: "0.1em" }}>
        v0.3 · CurryCast · Kandy
      </div>
    </aside>
  );
}
