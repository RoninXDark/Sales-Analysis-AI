import argparse
from pathlib import Path

from sales_analytics.reporting import generate_report_bundle


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate sales KPI tables, forecast files, and charts."
    )
    parser.add_argument(
        "source",
        nargs="?",
        default="data/sample_sales.csv",
        type=Path,
    )
    parser.add_argument(
        "--output",
        default=Path("reports"),
        type=Path,
    )
    parser.add_argument(
        "--charts",
        default=Path("docs/assets"),
        type=Path,
    )
    parser.add_argument(
        "--forecast-months",
        default=3,
        type=int,
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = generate_report_bundle(
        source=args.source,
        output_dir=args.output,
        chart_dir=args.charts,
        forecast_periods=args.forecast_months,
    )
    print(f"Generated reports for {summary['transactions']:,} transactions.")
    print(f"Total revenue: ${summary['total_revenue']:,.2f}")


if __name__ == "__main__":
    main()
