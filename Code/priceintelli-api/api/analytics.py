import numpy as np
import pandas as pd
from fastapi import APIRouter, Query
from api.db import execute_query

router = APIRouter()


@router.get("/forecast/{product_match_key}")
def get_price_forecast(
    product_match_key: str,
    days_ahead: int = Query(14, le=30),
    history_days: int = Query(60, le=180),
):
    # Forecast 14 days ahead with 95% CI
    sql = """
    SELECT crawl_date, AVG(price) AS avg_price
    FROM iphone_clean_products
    WHERE product_match_key = %(key)s
    AND crawl_date >= CURRENT_DATE - INTERVAL '%(days)s days'
    GROUP BY crawl_date
    ORDER BY crawl_date ASC
    """
    df = execute_query(sql, {"key": product_match_key, "days": history_days})
    if len(df) < 5:
        # Fallback neu chua du 10 ngay thi cho phep toi thieu 5 ngay hoac bao thieu data
        return {"error": "Not enough history data (need at least 5 days of history)"}

    prices = df["avg_price"].values
    dates = pd.to_datetime(df["crawl_date"])

    x = np.arange(len(prices))
    slope, intercept = np.polyfit(x, prices, 1)

    future_x = np.arange(len(prices), len(prices) + days_ahead)
    future_prices = slope * future_x + intercept

    residuals = prices - (slope * x + intercept)
    resid_std = np.std(residuals) if len(residuals) > 1 else 100000
    ci = 1.96 * resid_std * np.sqrt(np.arange(1, days_ahead + 1))

    future_dates = pd.date_range(
        start=dates.iloc[-1] + pd.Timedelta(days=1),
        periods=days_ahead,
        freq="D",
    )

    return {
        "product_match_key": product_match_key,
        "history": {
            "dates": dates.dt.strftime("%Y-%m-%d").tolist(),
            "prices": [float(p) for p in prices],
        },
        "forecast": {
            "dates": future_dates.strftime("%Y-%m-%d").tolist(),
            "prices": [round(float(p), 0) for p in future_prices],
            "lower": [round(float(max(0, p)), 0) for p in (future_prices - ci)],
            "upper": [round(float(p), 0) for p in (future_prices + ci)],
        },
        "trend": "up" if slope > 0 else "down",
    }


@router.get("/anomalies/{product_match_key}")
def get_anomalies_data(
    product_match_key: str,
    window: int = Query(14, ge=3, le=30),
    threshold: float = Query(2.0, ge=1.0, le=5.0),
):
    # Detect anomalies using rolling Z-score
    sql = """
    SELECT crawl_date, AVG(price) AS price
    FROM iphone_clean_products
    WHERE product_match_key = %(key)s
    AND crawl_date >= CURRENT_DATE - INTERVAL '90 days'
    GROUP BY crawl_date
    ORDER BY crawl_date ASC
    """
    df = execute_query(sql, {"key": product_match_key})
    if len(df) < window:
        return {"error": f"Need at least {window} days of data"}

    s = df.set_index("crawl_date")["price"]
    rolling_mean = s.rolling(window, min_periods=2).mean()
    rolling_std = s.rolling(window, min_periods=2).std().replace(0, 1)
    z = (s - rolling_mean) / rolling_std

    anomalies = df[z.abs() > threshold].copy()
    anomalies["z_score"] = z[z.abs() > threshold].values

    return {
        "product_match_key": product_match_key,
        "total_points": len(df),
        "anomaly_count": len(anomalies),
        "anomalies": anomalies.to_dict(orient="records"),
    }
