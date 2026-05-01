import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Home from "./pages/Home";
import Forecast from "./pages/Forecast";
import PrepList from "./pages/PrepList";
import WeatherImpact from "./pages/WeatherImpact";
import Backtest from "./pages/Backtest";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Home />} />
        <Route path="/forecast" element={<Forecast />} />
        <Route path="/prep" element={<PrepList />} />
        <Route path="/weather" element={<WeatherImpact />} />
        <Route path="/backtest" element={<Backtest />} />
      </Route>
    </Routes>
  );
}
