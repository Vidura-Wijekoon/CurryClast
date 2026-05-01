// CurryCast API client — talks to FastAPI backend.
// Uses Vite's /api proxy in dev (see vite.config.ts).

const BASE = import.meta.env.VITE_API_BASE || "/api";

export interface DailyForecast {
  date: string;
  yhat: number;
  yhat_lower: number;
  yhat_upper: number;
}

export interface PrepItem {
  date: string;
  item_canonical: string;
  prep_qty: number;
  unit: string;
}

export interface WeatherDay {
  date: string;
  temp_c: number;
  humidity: number;
  rain_mm: number;
  is_rainy: boolean;
  weather_main?: string;
}

export interface HourlyForecast {
  date: string;
  hour: number;
  item_canonical: string;
  yhat: number;
}

export interface PredictResponse {
  generated_at: string;
  city: string;
  daily_forecast: DailyForecast[];
  prep_list: PrepItem[];
  weather: WeatherDay[];
  hourly_forecast: HourlyForecast[];
}

export interface BacktestResponse {
  holdout_days: number;
  metrics: {
    wape: number;
    mape: number;
    rmse: number;
    stockout_rate: number;
  };
  savings: {
    naive_waste_lkr: number;
    smart_waste_lkr: number;
    savings_lkr: number;
  };
  per_item: { item_canonical: string; actual: number; predicted: number }[];
}

export interface RestaurantInfo {
  name: string;
  city: string;
  type: string;
  open_hour: number;
  close_hour: number;
  avg_cover_value_lkr: number;
}

async function jsonFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`API ${path} ${res.status}: ${text}`);
  }
  return res.json();
}

export const api = {
  health: () => jsonFetch<{ status: string; restaurant: string; version: string }>("/health"),
  restaurant: () => jsonFetch<RestaurantInfo>("/restaurant"),
  predict: (days = 7) =>
    jsonFetch<PredictResponse>("/predict", {
      method: "POST",
      body: JSON.stringify({ days }),
    }),
  backtest: (holdout_days = 30) =>
    jsonFetch<BacktestResponse>("/backtest", {
      method: "POST",
      body: JSON.stringify({ holdout_days }),
    }),
  weather: () => jsonFetch<WeatherDay[]>("/weather"),
};

export function formatLKR(amount: number, short = false): string {
  if (short) {
    if (Math.abs(amount) >= 1_000_000) return `LKR ${(amount / 1_000_000).toFixed(1)}M`;
    if (Math.abs(amount) >= 1_000) return `LKR ${(amount / 1_000).toFixed(0)}k`;
    return `LKR ${Math.round(amount)}`;
  }
  return `LKR ${Math.round(amount).toLocaleString()}`;
}

export interface TouristSeasonContext {
  season: "Peak" | "Shoulder" | "Low";
  index: number;
  note: string;
  upcoming?: string;
}

/** Sri Lanka west-coast tourist season signal based on SLTDA arrival patterns. */
export function getTouristSeason(month: number): TouristSeasonContext {
  if ([12, 1, 2, 3].includes(month)) {
    return {
      season: "Peak",
      index: 1.38,
      note: "European winter peak — Dec–Mar brings the highest international arrivals. Tourist-driven covers are up 30–40%. Fine-dining & tourist-facing menus see the strongest lift.",
      upcoming: month === 3 ? "Peak ends in April — plan inventory draw-down mid-March." : undefined,
    };
  }
  if ([4, 5].includes(month)) {
    return {
      season: "Shoulder",
      index: 1.08,
      note: "Post-peak shoulder. International arrivals tapering from March high. School New Year holidays (April) and Vesak (May) drive strong domestic covers.",
      upcoming: "SW monsoon begins June — international tourism softens, domestic traffic holds.",
    };
  }
  if ([6, 7, 8, 9].includes(month)) {
    return {
      season: "Low",
      index: 0.84,
      note: "SW monsoon season. International arrivals at annual low. East-coast properties see opposite peak. Colombo domestic & pilgrim traffic sustains base load.",
      upcoming: month >= 8 ? "Inter-monsoon shoulder starts October — arrivals recover toward December peak." : undefined,
    };
  }
  // Oct, Nov
  return {
    season: "Shoulder",
    index: 1.06,
    note: "Inter-monsoon recovery. Arrivals building ahead of December peak. Advance bookings for the festive season begin — worth over-prepping premium items.",
    upcoming: "Peak season from December — scale up buffet ratios in late November.",
  };
}

export function formatDate(iso: string, fmt: "long" | "short" = "long"): string {
  const d = new Date(iso + "T00:00:00");
  if (fmt === "short") {
    return d.toLocaleDateString("en-LK", { weekday: "short", day: "numeric", month: "short" });
  }
  return d.toLocaleDateString("en-LK", { weekday: "long", day: "numeric", month: "long", year: "numeric" });
}
