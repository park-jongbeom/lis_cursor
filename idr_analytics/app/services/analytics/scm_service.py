"""SCM demand forecast — Prophet primary, ARIMA(1,1,1) fallback."""

from __future__ import annotations

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from typing import Any

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from prophet import Prophet
from statsmodels.tsa.arima.model import ARIMA

from app.core.config import settings
from app.schemas.scm import ForecastItem, PredictionPoint

_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="scm_analytics")
logger = logging.getLogger(__name__)

_MIN_ROWS_PROPHET = 60


def _trend_from_yhat(yhat: NDArray[np.float64]) -> str:
    if len(yhat) < 2:
        return "stable"
    k = max(1, len(yhat) // 4)
    head = float(np.mean(yhat[:k]))
    tail = float(np.mean(yhat[-k:]))
    if tail > head * 1.02:
        return "increasing"
    if tail < head * 0.98:
        return "decreasing"
    return "stable"


def _seasonality_from_prophet(m: Prophet) -> dict[str, bool]:
    return {
        "weekly": bool(m.weekly_seasonality),
        "yearly": bool(m.yearly_seasonality),
    }


def _forecast_item_from_prophet(
    test_code: str,
    prep: pd.DataFrame,
    periods: int,
) -> ForecastItem:
    m = Prophet(changepoint_prior_scale=settings.PROPHET_CHANGEPOINT_SCALE)
    m.fit(prep)
    future = m.make_future_dataframe(periods=periods)
    fc = m.predict(future)
    tail = fc.tail(periods)
    predictions: list[PredictionPoint] = []
    for _, row in tail.iterrows():
        ds_val = row["ds"]
        if isinstance(ds_val, pd.Timestamp):
            ds_str = str(ds_val.date())
        else:
            ds_str = str(ds_val)[:10]
        predictions.append(
            PredictionPoint(
                ds=ds_str,
                yhat=float(row["yhat"]),
                yhat_lower=float(row["yhat_lower"]),
                yhat_upper=float(row["yhat_upper"]),
            )
        )
    yhat_arr = tail["yhat"].to_numpy(dtype=float)
    trend = _trend_from_yhat(yhat_arr)
    seasonality = _seasonality_from_prophet(m)
    return ForecastItem(
        test_code=test_code,
        predictions=predictions,
        trend_direction=trend,
        seasonality=seasonality,
    )


def _forecast_item_from_arima(test_code: str, prep: pd.DataFrame, periods: int) -> ForecastItem:
    y = prep["y"].astype(float).to_numpy()
    last_ts = prep["ds"].max()
    if not isinstance(last_ts, pd.Timestamp):
        last_ts = pd.to_datetime(last_ts)
    model = ARIMA(y, order=(1, 1, 1))
    res = model.fit()
    fc = res.get_forecast(steps=periods)
    mean = fc.predicted_mean
    conf = fc.conf_int(alpha=0.2)
    lower = conf.iloc[:, 0].to_numpy(dtype=float)
    upper = conf.iloc[:, 1].to_numpy(dtype=float)
    predictions: list[PredictionPoint] = []
    for i in range(periods):
        ds = last_ts + timedelta(days=i + 1)
        predictions.append(
            PredictionPoint(
                ds=str(ds.date()),
                yhat=float(mean[i]),
                yhat_lower=float(lower[i]),
                yhat_upper=float(upper[i]),
            )
        )
    yhat_arr = mean.astype(float)
    trend = _trend_from_yhat(yhat_arr)
    return ForecastItem(
        test_code=test_code,
        predictions=predictions,
        trend_direction=trend,
        seasonality={"weekly": False, "yearly": False},
    )


def _forecast_one_group(
    test_code: str,
    sub: pd.DataFrame,
    target_col: str,
    date_col: str,
    periods: int,
) -> ForecastItem | None:
    prep = sub[[date_col, target_col]].copy()
    prep = prep.rename(columns={date_col: "ds", target_col: "y"})
    prep["ds"] = pd.to_datetime(prep["ds"], errors="coerce")
    prep = prep.dropna(subset=["ds", "y"])
    prep = prep.sort_values("ds")
    if len(prep) < 2:
        logger.warning("Skipping group %s: fewer than 2 valid rows", test_code)
        return None
    if len(prep) < _MIN_ROWS_PROPHET:
        try:
            return _forecast_item_from_arima(test_code, prep, periods)
        except Exception:
            logger.exception("ARIMA failed for group %s", test_code)
            return None
    try:
        return _forecast_item_from_prophet(test_code, prep, periods)
    except Exception:
        logger.warning("Prophet failed for group %s, trying ARIMA", test_code, exc_info=True)
        try:
            return _forecast_item_from_arima(test_code, prep, periods)
        except Exception:
            logger.exception("ARIMA failed for group %s after Prophet", test_code)
            return None


def _filter_by_test_codes(df: pd.DataFrame, group_col: str, test_codes: list[str] | None) -> pd.DataFrame:
    if not test_codes:
        return df
    codes = {str(c) for c in test_codes}
    return df[df[group_col].astype(str).isin(codes)].copy()


def _sync_forecast(
    df: pd.DataFrame,
    target_col: str,
    date_col: str,
    group_col: str,
    periods: int,
) -> list[ForecastItem]:
    work = df.copy()
    for col in (target_col, date_col, group_col):
        if col not in work.columns:
            msg = f"Column {col!r} not in DataFrame"
            raise KeyError(msg)
    out: list[ForecastItem] = []
    for key, sub in work.groupby(group_col, sort=False):
        test_code = str(key)
        item = _forecast_one_group(test_code, sub, target_col, date_col, periods)
        if item is not None:
            out.append(item)
    return out


class SCMService:
    async def forecast(
        self,
        df: pd.DataFrame,
        target_col: str,
        date_col: str,
        group_col: str,
        periods: int,
    ) -> list[ForecastItem]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            _executor,
            lambda: _sync_forecast(df, target_col, date_col, group_col, periods),
        )

    async def restock_alert_report(
        self,
        df: pd.DataFrame,
        target_col: str,
        date_col: str,
        group_col: str,
        *,
        test_codes: list[str] | None = None,
        forecast_days: int = 30,
    ) -> dict[str, Any]:
        work = _filter_by_test_codes(df, group_col, test_codes)
        forecasts = await self.forecast(work, target_col, date_col, group_col, forecast_days)
        items: list[dict[str, object]] = []
        for item in forecasts:
            preds = item.predictions
            if not preds:
                continue
            last_yhat = preds[-1].yhat
            if len(preds) >= 2:
                tail = preds[:-1][-6:] if len(preds) > 7 else preds[:-1]
                prev_avg = sum(p.yhat for p in tail) / max(len(tail), 1)
            else:
                prev_avg = last_yhat
            alert = prev_avg > 0 and last_yhat > prev_avg * 1.15
            items.append(
                {
                    "test_code": item.test_code,
                    "restock_suggested": alert,
                    "predicted_last_period_qty": last_yhat,
                    "recent_avg_qty": prev_avg,
                }
            )
        restock_alerts = sum(1 for x in items if x["restock_suggested"])
        return {
            "forecasts": forecasts,
            "restock_alerts": restock_alerts,
            "items": items,
        }

    async def seasonal_pattern_report(
        self,
        df: pd.DataFrame,
        target_col: str,
        date_col: str,
        group_col: str,
        *,
        test_codes: list[str] | None = None,
        forecast_days: int = 30,
    ) -> dict[str, Any]:
        work = _filter_by_test_codes(df, group_col, test_codes)
        forecasts = await self.forecast(work, target_col, date_col, group_col, forecast_days)
        patterns = [
            {
                "test_code": f.test_code,
                "seasonality": f.seasonality,
                "trend_direction": f.trend_direction,
            }
            for f in forecasts
        ]
        return {"patterns": patterns, "forecast_days": forecast_days}


scm_service = SCMService()
