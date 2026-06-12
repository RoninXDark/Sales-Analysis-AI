from pathlib import Path

from sales_analytics.reporting import generate_report_bundle


def main() -> None:
    source = Path("data/sample_sales.csv")
    summary = generate_report_bundle(source)
    print("Sales report generated in reports/ and docs/assets/.")
    print(f"Total revenue: ${summary['total_revenue']:,.2f}")
    print(f"Top product: {summary['top_product']}")


if __name__ == "__main__":
    main()
