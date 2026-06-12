import pandas as pd
import pytest

from sales_analytics.analysis import (
    compute_kpis,
    detect_monthly_anomalies,
    forecast_monthly_revenue,
    monthly_revenue,
    prepare_sales_data,
    product_performance,
)


@pytest.fixture
def sales_frame() -> pd.DataFrame:
    return prepare_sales_data(
        pd.DataFrame(
            {
                "Date": [
                    "2025-01-01",
                    "2025-01-10",
                    "2025-02-01",
                    "2025-03-01",
                ],
                "Product": ["Laptop", "Mouse", "Laptop", "Mouse"],
                "Revenue": [1000, 50, 1200, 70],
            }
        )
    )


def test_prepare_sales_data_rejects_missing_columns() -> None:
    with pytest.raises(ValueError, match="Missing required columns"):
        prepare_sales_data(pd.DataFrame({"Date": ["2025-01-01"]}))


def test_compute_kpis(sales_frame: pd.DataFrame) -> None:
    kpis = compute_kpis(sales_frame)

    assert kpis["total_revenue"] == 2320
    assert kpis["transactions"] == 4
    assert kpis["top_product"] == "Laptop"


def test_monthly_and_product_aggregations(
    sales_frame: pd.DataFrame,
) -> None:
    monthly = monthly_revenue(sales_frame)
    products = product_performance(sales_frame)

    assert monthly["Revenue"].tolist() == [1050, 1200, 70]
    assert products.iloc[0]["Product"] == "Laptop"
    assert products["RevenueShare"].sum() == pytest.approx(1.0)


def test_forecast_returns_requested_periods(
    sales_frame: pd.DataFrame,
) -> None:
    monthly = monthly_revenue(sales_frame)
    forecast, metrics = forecast_monthly_revenue(monthly, periods=2)

    assert len(forecast) == 2
    assert {"r2", "rmse", "slope"} == set(metrics)
    assert (forecast["ForecastRevenue"] >= 0).all()


def test_anomaly_output_has_flags(sales_frame: pd.DataFrame) -> None:
    result = detect_monthly_anomalies(monthly_revenue(sales_frame))

    assert "ZScore" in result
    assert "IsAnomaly" in result
