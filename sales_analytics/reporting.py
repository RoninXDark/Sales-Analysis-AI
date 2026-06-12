import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from sales_analytics.analysis import (
    compute_kpis,
    detect_monthly_anomalies,
    forecast_monthly_revenue,
    monthly_revenue,
    prepare_sales_data,
    product_performance,
)


def _style_axes(axis: plt.Axes) -> None:
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    axis.grid(axis="y", alpha=0.2)


def generate_report_bundle(
    source: str | Path,
    output_dir: str | Path = "reports",
    chart_dir: str | Path = "docs/assets",
    forecast_periods: int = 3,
) -> dict[str, object]:
    output_path = Path(output_dir)
    charts_path = Path(chart_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    charts_path.mkdir(parents=True, exist_ok=True)

    frame = prepare_sales_data(source)
    monthly = monthly_revenue(frame)
    products = product_performance(frame)
    anomalies = detect_monthly_anomalies(monthly)
    forecast, model_metrics = forecast_monthly_revenue(
        monthly,
        periods=forecast_periods,
    )
    kpis = compute_kpis(frame)

    monthly.to_csv(output_path / "monthly_revenue.csv", index=False)
    products.to_csv(output_path / "product_performance.csv", index=False)
    anomalies.to_csv(output_path / "monthly_anomalies.csv", index=False)
    forecast.to_csv(output_path / "revenue_forecast.csv", index=False)

    summary = {
        **kpis,
        "forecast_model": model_metrics,
        "anomaly_months": int(anomalies["IsAnomaly"].sum()),
    }
    (output_path / "summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )

    figure, axis = plt.subplots(figsize=(10, 5.5))
    axis.plot(
        monthly["Month"],
        monthly["Revenue"],
        color="#167d9a",
        linewidth=2.5,
        marker="o",
    )
    axis.set_title("Monthly Revenue Trend")
    axis.set_ylabel("Revenue (USD)")
    _style_axes(axis)
    figure.autofmt_xdate()
    figure.tight_layout()
    figure.savefig(charts_path / "monthly_revenue.png", dpi=160)
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(10, 5.5))
    axis.bar(
        products["Product"],
        products["Revenue"],
        color=["#167d9a", "#32a287", "#d9a441", "#6b7fd7", "#c86b6b"],
    )
    axis.set_title("Revenue by Product")
    axis.set_ylabel("Revenue (USD)")
    _style_axes(axis)
    figure.tight_layout()
    figure.savefig(charts_path / "product_performance.png", dpi=160)
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(10, 5.5))
    axis.plot(
        monthly["Month"],
        monthly["Revenue"],
        label="Actual",
        color="#167d9a",
        linewidth=2.5,
    )
    axis.plot(
        forecast["Month"],
        forecast["ForecastRevenue"],
        label="Forecast",
        color="#d97941",
        linewidth=2.5,
        marker="o",
    )
    axis.fill_between(
        forecast["Month"],
        forecast["LowerBound"],
        forecast["UpperBound"],
        color="#d97941",
        alpha=0.18,
        label="80% interval",
    )
    axis.set_title("Revenue Forecast")
    axis.set_ylabel("Revenue (USD)")
    axis.legend(frameon=False)
    _style_axes(axis)
    figure.autofmt_xdate()
    figure.tight_layout()
    figure.savefig(charts_path / "revenue_forecast.png", dpi=160)
    plt.close(figure)

    return summary
