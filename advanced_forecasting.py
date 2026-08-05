"""
Advanced Forecasting v4.4 — ETS, SARIMA, and Ensemble Models
Time series forecasting for demand, inventory, and operations.
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class ForecastResult:
    dates: List[datetime]
    forecast: List[float]
    lower_bound: List[float]
    upper_bound: List[float]
    model_name: str
    mape: Optional[float] = None
    rmse: Optional[float] = None

class ForecastingEngine:
    def __init__(self):
        self.models = ["ets", "sarima", "naive", "ensemble"]
        self.history: List[Tuple[datetime, float]] = []

    def add_history(self, date: datetime, value: float):
        self.history.append((date, value))
        self.history.sort(key=lambda x: x[0])

    def _to_series(self) -> pd.Series:
        if not self.history:
            return pd.Series(dtype=float)
        dates, values = zip(*self.history)
        return pd.Series(values, index=pd.DatetimeIndex(dates))

    # ── ETS (Error, Trend, Seasonality) ──────────────────────
    def ets_forecast(self, horizon: int = 30, alpha: float = 0.3, beta: float = 0.1, gamma: float = 0.1,
                     season_length: int = 7) -> ForecastResult:
        series = self._to_series()
        if len(series) < season_length * 2:
            return self.naive_forecast(horizon)

        values = series.values
        n = len(values)

        # Holt-Winters additive
        level = values[:season_length].mean()
        trend = (values[season_length:2*season_length].mean() - level) / season_length
        seasonal = values[:season_length] - level

        forecast_vals = []
        for h in range(1, horizon + 1):
            idx = (n + h - 1) % season_length
            pred = level + h * trend + seasonal[idx]
            forecast_vals.append(pred)

            if n + h - 1 < len(values):
                actual = values[n + h - 1] if n + h - 1 < len(values) else pred
                level = alpha * (actual - seasonal[idx]) + (1 - alpha) * (level + trend)
                trend = beta * (level - (level - trend)) + (1 - beta) * trend
                seasonal[idx] = gamma * (actual - level) + (1 - gamma) * seasonal[idx]

        std = np.std(values)
        dates = [series.index[-1] + timedelta(days=i+1) for i in range(horizon)]
        return ForecastResult(
            dates=dates,
            forecast=forecast_vals,
            lower_bound=[f - 1.96 * std for f in forecast_vals],
            upper_bound=[f + 1.96 * std for f in forecast_vals],
            model_name="ETS"
        )

    # ── SARIMA (Simplified) ──────────────────────────────────
    def sarima_forecast(self, horizon: int = 30, p: int = 1, d: int = 1, q: int = 1,
                        P: int = 1, D: int = 1, Q: int = 1, m: int = 7) -> ForecastResult:
        series = self._to_series()
        if len(series) < m * 3:
            return self.naive_forecast(horizon)

        values = np.array(series.values, dtype=float)
        # Simple differencing
        diff = np.diff(values, n=d)

        # AR(1) on differenced series
        phi = np.corrcoef(diff[:-1], diff[1:])[0, 1] if len(diff) > 1 else 0.5
        phi = max(-0.99, min(0.99, phi))

        last_vals = values[-d:].tolist() if d > 0 else [values[-1]]
        forecast_vals = []

        for h in range(1, horizon + 1):
            if d == 1:
                pred = last_vals[-1] + phi * (last_vals[-1] - last_vals[-2]) if len(last_vals) > 1 else last_vals[-1]
            else:
                pred = last_vals[-1] * (1 + phi * 0.01)
            forecast_vals.append(pred)
            last_vals.append(pred)

        std = np.std(values)
        dates = [series.index[-1] + timedelta(days=i+1) for i in range(horizon)]
        return ForecastResult(
            dates=dates,
            forecast=forecast_vals,
            lower_bound=[f - 1.96 * std for f in forecast_vals],
            upper_bound=[f + 1.96 * std for f in forecast_vals],
            model_name="SARIMA"
        )

    # ── Naive / Seasonal Naive ───────────────────────────────
    def naive_forecast(self, horizon: int = 30) -> ForecastResult:
        series = self._to_series()
        if len(series) == 0:
            dates = [datetime.now() + timedelta(days=i+1) for i in range(horizon)]
            return ForecastResult(dates=dates, forecast=[0]*horizon, lower_bound=[0]*horizon,
                                  upper_bound=[0]*horizon, model_name="Naive")
        last_val = series.values[-1]
        std = np.std(series.values) if len(series) > 1 else last_val * 0.1
        dates = [series.index[-1] + timedelta(days=i+1) for i in range(horizon)]
        return ForecastResult(
            dates=dates,
            forecast=[last_val] * horizon,
            lower_bound=[last_val - 1.96 * std] * horizon,
            upper_bound=[last_val + 1.96 * std] * horizon,
            model_name="Naive"
        )

    # ── Ensemble ─────────────────────────────────────────────
    def ensemble_forecast(self, horizon: int = 30, weights: Optional[Dict[str, float]] = None) -> ForecastResult:
        w = weights or {"ets": 0.4, "sarima": 0.4, "naive": 0.2}
        ets_res = self.ets_forecast(horizon)
        sarima_res = self.sarima_forecast(horizon)
        naive_res = self.naive_forecast(horizon)

        ensemble = []
        lower = []
        upper = []
        for i in range(horizon):
            val = (w["ets"] * ets_res.forecast[i] +
                   w["sarima"] * sarima_res.forecast[i] +
                   w["naive"] * naive_res.forecast[i])
            ensemble.append(val)
            lower.append(min(ets_res.lower_bound[i], sarima_res.lower_bound[i], naive_res.lower_bound[i]))
            upper.append(max(ets_res.upper_bound[i], sarima_res.upper_bound[i], naive_res.upper_bound[i]))

        return ForecastResult(
            dates=ets_res.dates,
            forecast=ensemble,
            lower_bound=lower,
            upper_bound=upper,
            model_name="Ensemble"
        )

    def forecast(self, model: str = "auto", horizon: int = 30) -> ForecastResult:
        if model == "auto":
            series = self._to_series()
            if len(series) < 14:
                return self.naive_forecast(horizon)
            elif len(series) < 60:
                return self.ets_forecast(horizon)
            else:
                return self.ensemble_forecast(horizon)
        elif model == "ets":
            return self.ets_forecast(horizon)
        elif model == "sarima":
            return self.sarima_forecast(horizon)
        elif model == "naive":
            return self.naive_forecast(horizon)
        else:
            return self.ensemble_forecast(horizon)

    def evaluate_accuracy(self, actual: List[float], predicted: List[float]) -> Dict:
        actual = np.array(actual)
        predicted = np.array(predicted)
        mape = np.mean(np.abs((actual - predicted) / np.maximum(actual, 1))) * 100
        rmse = np.sqrt(np.mean((actual - predicted) ** 2))
        mae = np.mean(np.abs(actual - predicted))
        return {"mape": round(mape, 2), "rmse": round(rmse, 2), "mae": round(mae, 2)}
