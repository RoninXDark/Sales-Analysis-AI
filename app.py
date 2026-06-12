from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from sales_analytics import (
    compute_kpis,
    detect_monthly_anomalies,
    forecast_monthly_revenue,
    monthly_revenue,
    prepare_sales_data,
    product_performance,
)


DEFAULT_DATA = Path(__file__).parent / "data" / "sample_sales.csv"


st.set_page_config(
    page_title="Sales Performance Analytics",
    layout="wide",
)


@st.cache_data
def load_default_data() -> pd.DataFrame:
    return prepare_sales_data(DEFAULT_DATA)


def money(value: float) -> str:
    return f"${value:,.0f}"


st.title("Sales Performance Analytics")
st.caption(
    "Interactive KPI monitoring, product analysis, anomaly detection, "
    "and short-term revenue forecasting."
)

uploaded_file = st.sidebar.file_uploader(
    "Upload sales CSV",
    type=["csv"],
    help="Required columns: Date, Product, Revenue",
)

try:
    source_frame = (
        prepare_sales_data(uploaded_file)
        if uploaded_file is not None
        else load_default_data()
    )
except ValueError as exc:
    st.error(str(exc))
    st.stop()

date_min = source_frame["Date"].min().date()
date_max = source_frame["Date"].max().date()
date_range = st.sidebar.date_input(
    "Date range",
    value=(date_min, date_max),
    min_value=date_min,
    max_value=date_max,
)
products = sorted(source_frame["Product"].unique())
selected_products = st.sidebar.multiselect(
    "Products",
    options=products,
    default=products,
)

if len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = end_date = date_range[0]

frame = source_frame[
    source_frame["Date"].dt.date.between(start_date, end_date)
    & source_frame["Product"].isin(selected_products)
].copy()

if frame.empty:
    st.warning("No rows match the selected filters.")
    st.stop()

kpis = compute_kpis(frame)
monthly = monthly_revenue(frame)
product_table = product_performance(frame)
anomalies = detect_monthly_anomalies(monthly)

metric_columns = st.columns(4)
metric_columns[0].metric("Total revenue", money(kpis["total_revenue"]))
metric_columns[1].metric("Transactions", f"{kpis['transactions']:,}")
metric_columns[2].metric(
    "Average order value",
    money(kpis["average_order_value"]),
)
metric_columns[3].metric("Top product", kpis["top_product"])

overview_tab, products_tab, forecast_tab, quality_tab = st.tabs(
    ["Overview", "Products", "Forecast", "Data quality"]
)

with overview_tab:
    revenue_chart = px.line(
        monthly,
        x="Month",
        y="Revenue",
        markers=True,
        title="Monthly revenue",
    )
    revenue_chart.update_traces(line_color="#167d9a")
    revenue_chart.update_layout(
        xaxis_title="",
        yaxis_title="Revenue (USD)",
        hovermode="x unified",
    )
    st.plotly_chart(revenue_chart, use_container_width=True)

    transaction_chart = px.bar(
        monthly,
        x="Month",
        y="Transactions",
        title="Monthly transaction volume",
        color_discrete_sequence=["#32a287"],
    )
    transaction_chart.update_layout(xaxis_title="", yaxis_title="Transactions")
    st.plotly_chart(transaction_chart, use_container_width=True)

with products_tab:
    product_chart = px.bar(
        product_table,
        x="Product",
        y="Revenue",
        color="Revenue",
        color_continuous_scale="Teal",
        title="Revenue contribution by product",
    )
    product_chart.update_layout(
        xaxis_title="",
        yaxis_title="Revenue (USD)",
        coloraxis_showscale=False,
    )
    st.plotly_chart(product_chart, use_container_width=True)

    display_products = product_table.copy()
    display_products["RevenueShare"] = display_products[
        "RevenueShare"
    ].map(lambda value: f"{value:.1%}")
    st.dataframe(
        display_products,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Revenue": st.column_config.NumberColumn(format="$%.2f"),
            "AverageOrderValue": st.column_config.NumberColumn(format="$%.2f"),
        },
    )

with forecast_tab:
    forecast_periods = st.slider("Forecast horizon (months)", 1, 6, 3)
    if len(monthly) < 3:
        st.info("At least three months are required for forecasting.")
    else:
        forecast, model_metrics = forecast_monthly_revenue(
            monthly,
            periods=forecast_periods,
        )
        figure = go.Figure()
        figure.add_trace(
            go.Scatter(
                x=monthly["Month"],
                y=monthly["Revenue"],
                name="Actual",
                line={"color": "#167d9a", "width": 3},
            )
        )
        figure.add_trace(
            go.Scatter(
                x=forecast["Month"],
                y=forecast["UpperBound"],
                mode="lines",
                line={"width": 0},
                showlegend=False,
            )
        )
        figure.add_trace(
            go.Scatter(
                x=forecast["Month"],
                y=forecast["LowerBound"],
                mode="lines",
                line={"width": 0},
                fill="tonexty",
                fillcolor="rgba(217, 121, 65, 0.18)",
                name="80% interval",
            )
        )
        figure.add_trace(
            go.Scatter(
                x=forecast["Month"],
                y=forecast["ForecastRevenue"],
                name="Forecast",
                line={"color": "#d97941", "width": 3, "dash": "dash"},
            )
        )
        figure.update_layout(
            title="Linear revenue forecast",
            xaxis_title="",
            yaxis_title="Revenue (USD)",
            hovermode="x unified",
        )
        st.plotly_chart(figure, use_container_width=True)
        left, middle, right = st.columns(3)
        left.metric("Model R2", f"{model_metrics['r2']:.3f}")
        middle.metric("RMSE", money(model_metrics["rmse"]))
        right.metric("Monthly trend", money(model_metrics["slope"]))
        st.download_button(
            "Download forecast CSV",
            forecast.to_csv(index=False).encode("utf-8"),
            file_name="revenue_forecast.csv",
            mime="text/csv",
        )

with quality_tab:
    anomaly_count = int(anomalies["IsAnomaly"].sum())
    st.metric("Anomalous months", anomaly_count)
    st.caption(
        "Monthly revenue is flagged when its absolute z-score is at least 2.0."
    )
    st.dataframe(
        anomalies,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Revenue": st.column_config.NumberColumn(format="$%.2f"),
            "ZScore": st.column_config.NumberColumn(format="%.2f"),
        },
    )
    st.download_button(
        "Download cleaned data",
        frame.drop(columns=["Month"]).to_csv(index=False).encode("utf-8"),
        file_name="cleaned_sales_data.csv",
        mime="text/csv",
    )
