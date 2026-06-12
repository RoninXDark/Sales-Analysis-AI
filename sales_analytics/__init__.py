"""Reusable sales analytics engine."""

from sales_analytics.analysis import (
    compute_kpis,
    detect_monthly_anomalies,
    forecast_monthly_revenue,
    monthly_revenue,
    prepare_sales_data,
    product_performance,
)

__all__ = [
    "compute_kpis",
    "detect_monthly_anomalies",
    "forecast_monthly_revenue",
    "monthly_revenue",
    "prepare_sales_data",
    "product_performance",
]
