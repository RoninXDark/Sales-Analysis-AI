from pathlib import Path
from typing import IO

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score


REQUIRED_COLUMNS = {"Date", "Product", "Revenue"}


def prepare_sales_data(
    source: str | Path | IO[bytes] | pd.DataFrame,
) -> pd.DataFrame:
    if isinstance(source, pd.DataFrame):
        frame = source.copy()
    else:
        frame = pd.read_csv(source)

    frame.columns = [str(column).strip() for column in frame.columns]
    missing = REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        missing_text = ", ".join(sorted(missing))
        raise ValueError(f"Missing required columns: {missing_text}")

    frame = frame.loc[:, ["Date", "Product", "Revenue"]].copy()
    frame["Date"] = pd.to_datetime(frame["Date"], errors="coerce")
    frame["Product"] = frame["Product"].astype("string").str.strip()
    frame["Revenue"] = pd.to_numeric(frame["Revenue"], errors="coerce")
    frame = frame.dropna(subset=["Date", "Product", "Revenue"])
    frame = frame[(frame["Product"] != "") & (frame["Revenue"] >= 0)]
    frame = frame.sort_values("Date").reset_index(drop=True)

    if frame.empty:
        raise ValueError("No valid sales rows remain after data cleaning.")

    frame["Month"] = frame["Date"].dt.to_period("M").dt.to_timestamp()
    return frame


def compute_kpis(frame: pd.DataFrame) -> dict[str, object]:
    revenue_by_product = (
        frame.groupby("Product", as_index=False)["Revenue"]
        .sum()
        .sort_values("Revenue", ascending=False)
    )
    top_row = revenue_by_product.iloc[0]
    total_revenue = float(frame["Revenue"].sum())

    return {
        "total_revenue": total_revenue,
        "transactions": int(len(frame)),
        "average_order_value": float(frame["Revenue"].mean()),
        "top_product": str(top_row["Product"]),
        "top_product_revenue": float(top_row["Revenue"]),
        "start_date": frame["Date"].min().date().isoformat(),
        "end_date": frame["Date"].max().date().isoformat(),
    }


def monthly_revenue(frame: pd.DataFrame) -> pd.DataFrame:
    return (
        frame.groupby("Month", as_index=False)
        .agg(Revenue=("Revenue", "sum"), Transactions=("Revenue", "size"))
        .sort_values("Month")
        .reset_index(drop=True)
    )


def product_performance(frame: pd.DataFrame) -> pd.DataFrame:
    result = (
        frame.groupby("Product", as_index=False)
        .agg(
            Revenue=("Revenue", "sum"),
            Transactions=("Revenue", "size"),
            AverageOrderValue=("Revenue", "mean"),
        )
        .sort_values("Revenue", ascending=False)
        .reset_index(drop=True)
    )
    total = result["Revenue"].sum()
    result["RevenueShare"] = np.where(
        total > 0,
        result["Revenue"] / total,
        0.0,
    )
    return result


def detect_monthly_anomalies(
    monthly: pd.DataFrame,
    threshold: float = 2.0,
) -> pd.DataFrame:
    result = monthly.copy()
    std = float(result["Revenue"].std(ddof=0))
    if std == 0 or np.isnan(std):
        result["ZScore"] = 0.0
    else:
        result["ZScore"] = (
            result["Revenue"] - result["Revenue"].mean()
        ) / std
    result["IsAnomaly"] = result["ZScore"].abs() >= threshold
    return result


def forecast_monthly_revenue(
    monthly: pd.DataFrame,
    periods: int = 3,
) -> tuple[pd.DataFrame, dict[str, float]]:
    if periods < 1:
        raise ValueError("Forecast periods must be at least 1.")
    if len(monthly) < 3:
        raise ValueError("At least three months are required for forecasting.")

    x = np.arange(len(monthly), dtype=float).reshape(-1, 1)
    y = monthly["Revenue"].to_numpy(dtype=float)
    model = LinearRegression()
    model.fit(x, y)

    fitted = model.predict(x)
    residuals = y - fitted
    rmse = float(np.sqrt(np.mean(np.square(residuals))))
    score = float(r2_score(y, fitted))

    future_x = np.arange(
        len(monthly),
        len(monthly) + periods,
        dtype=float,
    ).reshape(-1, 1)
    predictions = np.maximum(model.predict(future_x), 0.0)
    future_months = pd.date_range(
        monthly["Month"].max() + pd.offsets.MonthBegin(1),
        periods=periods,
        freq="MS",
    )

    forecast = pd.DataFrame(
        {
            "Month": future_months,
            "ForecastRevenue": predictions,
            "LowerBound": np.maximum(predictions - 1.28 * rmse, 0.0),
            "UpperBound": predictions + 1.28 * rmse,
        }
    )
    metrics = {
        "r2": score,
        "rmse": rmse,
        "slope": float(model.coef_[0]),
    }
    return forecast, metrics
