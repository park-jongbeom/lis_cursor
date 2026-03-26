"""SCMService 단위 테스트 — Prophet/ARIMA mock."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from app.services.analytics.scm_service import (
    _trend_from_yhat,
    scm_service,
)

# ── _trend_from_yhat ───────────────────────────────────────────────────────────


def test_trend_increasing() -> None:
    """S-01: 상승 배열 → 'increasing'."""
    arr = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0], dtype=float)
    assert _trend_from_yhat(arr) == "increasing"


def test_trend_decreasing() -> None:
    """S-02: 하락 배열 → 'decreasing'."""
    arr = np.array([8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0], dtype=float)
    assert _trend_from_yhat(arr) == "decreasing"


def test_trend_stable() -> None:
    """S-03: 평탄 배열 → 'stable'."""
    arr = np.array([5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0], dtype=float)
    assert _trend_from_yhat(arr) == "stable"


def test_trend_single_element() -> None:
    """S-04: 길이 1 → 'stable'."""
    arr = np.array([10.0], dtype=float)
    assert _trend_from_yhat(arr) == "stable"


# ── SCMService.forecast — Prophet mock ────────────────────────────────────────


def _make_prophet_forecast_df(periods: int) -> pd.DataFrame:
    dates = pd.date_range("2026-04-01", periods=periods)
    return pd.DataFrame(
        {
            "ds": dates,
            "yhat": [float(i + 100) for i in range(periods)],
            "yhat_lower": [float(i + 90) for i in range(periods)],
            "yhat_upper": [float(i + 110) for i in range(periods)],
            "trend": [float(i + 100) for i in range(periods)],
        }
    )


def _make_scm_df(n_rows: int = 80, group: str = "BRCA1") -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=n_rows, freq="D")
    return pd.DataFrame(
        {
            "order_date": dates.strftime("%Y-%m-%d"),
            "test_code": [group] * n_rows,
            "qty": np.random.default_rng(42).integers(10, 100, n_rows).astype(float),
        }
    )


@pytest.mark.asyncio
async def test_forecast_prophet_path() -> None:
    """S-05: 행 수 60 이상 → Prophet 경로, ForecastItem 반환."""
    df = _make_scm_df(n_rows=80)
    periods = 5

    mock_prophet = MagicMock()
    mock_prophet.return_value = mock_prophet
    mock_prophet.fit.return_value = mock_prophet
    mock_prophet.weekly_seasonality = True
    mock_prophet.yearly_seasonality = True
    mock_prophet.make_future_dataframe.return_value = pd.DataFrame(
        {"ds": pd.date_range("2026-01-01", periods=80 + periods)}
    )
    mock_prophet.predict.return_value = _make_prophet_forecast_df(80 + periods)

    with patch("app.services.analytics.scm_service.Prophet", mock_prophet):
        result = await scm_service.forecast(df, "qty", "order_date", "test_code", periods)

    assert len(result) == 1
    assert result[0].test_code == "BRCA1"
    assert len(result[0].predictions) == periods


@pytest.mark.asyncio
async def test_forecast_arima_path_small_group() -> None:
    """S-06: 행 수 60 미만 → ARIMA 경로."""
    df = _make_scm_df(n_rows=30)

    mock_arima_instance = MagicMock()
    mock_arima_instance.fit.return_value = mock_arima_instance
    fc_mock = MagicMock()
    fc_mock.predicted_mean = np.array([100.0, 101.0, 102.0])
    conf_df = pd.DataFrame({"lower": [90.0, 91.0, 92.0], "upper": [110.0, 111.0, 112.0]})
    fc_mock.conf_int.return_value = conf_df
    mock_arima_instance.get_forecast.return_value = fc_mock

    mock_arima_cls = MagicMock(return_value=mock_arima_instance)

    with patch("app.services.analytics.scm_service.ARIMA", mock_arima_cls):
        result = await scm_service.forecast(df, "qty", "order_date", "test_code", 3)

    assert len(result) == 1
    assert result[0].test_code == "BRCA1"
    mock_arima_cls.assert_called_once()


@pytest.mark.asyncio
async def test_forecast_prophet_exception_falls_back_to_arima() -> None:
    """S-07: Prophet 예외 → ARIMA 폴백."""
    df = _make_scm_df(n_rows=80)

    mock_prophet = MagicMock()
    mock_prophet.return_value = mock_prophet
    mock_prophet.fit.side_effect = RuntimeError("prophet error")

    mock_arima_instance = MagicMock()
    mock_arima_instance.fit.return_value = mock_arima_instance
    fc_mock = MagicMock()
    fc_mock.predicted_mean = np.array([100.0, 101.0])
    conf_df = pd.DataFrame({"lower": [90.0, 91.0], "upper": [110.0, 111.0]})
    fc_mock.conf_int.return_value = conf_df
    mock_arima_instance.get_forecast.return_value = fc_mock
    mock_arima_cls = MagicMock(return_value=mock_arima_instance)

    with patch("app.services.analytics.scm_service.Prophet", mock_prophet):
        with patch("app.services.analytics.scm_service.ARIMA", mock_arima_cls):
            result = await scm_service.forecast(df, "qty", "order_date", "test_code", 2)

    mock_arima_cls.assert_called_once()
    assert len(result) == 1


@pytest.mark.asyncio
async def test_forecast_missing_column_raises() -> None:
    """S-08: 필수 컬럼 누락 → KeyError."""
    df = pd.DataFrame({"a": [1, 2, 3]})
    with pytest.raises(KeyError):
        await scm_service.forecast(df, "qty", "order_date", "test_code", 5)


@pytest.mark.asyncio
async def test_forecast_two_groups() -> None:
    """S-09: 그룹 2개 → 결과 리스트 길이 2."""
    df1 = _make_scm_df(n_rows=30, group="BRCA1")
    df2 = _make_scm_df(n_rows=30, group="HPV")
    df = pd.concat([df1, df2], ignore_index=True)

    mock_arima_instance = MagicMock()
    mock_arima_instance.fit.return_value = mock_arima_instance
    fc_mock = MagicMock()
    fc_mock.predicted_mean = np.array([100.0, 101.0, 102.0])
    conf_df = pd.DataFrame({"lower": [90.0, 91.0, 92.0], "upper": [110.0, 111.0, 112.0]})
    fc_mock.conf_int.return_value = conf_df
    mock_arima_instance.get_forecast.return_value = fc_mock
    mock_arima_cls = MagicMock(return_value=mock_arima_instance)

    with patch("app.services.analytics.scm_service.ARIMA", mock_arima_cls):
        result = await scm_service.forecast(df, "qty", "order_date", "test_code", 3)

    assert len(result) == 2
    codes = {item.test_code for item in result}
    assert codes == {"BRCA1", "HPV"}
