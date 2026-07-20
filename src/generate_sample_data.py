import csv
import random
from datetime import date, timedelta
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

random.seed(20260720)

REGIONS = ["Guangzhou", "Shenzhen", "Shanghai", "Beijing", "Chengdu", "Hangzhou"]
CHANNELS = ["organic", "paid_search", "social", "referral", "app_store"]
CATEGORIES = {
    "beauty": (39, 299),
    "electronics": (99, 1299),
    "home": (29, 499),
    "sports": (49, 599),
    "fashion": (59, 699),
    "food": (19, 199),
}
STATUSES = ["paid", "paid", "paid", "paid", "cancelled", "refunded"]


def random_date(start: date, end: date) -> date:
    return start + timedelta(days=random.randint(0, (end - start).days))


def write_customers(customer_count: int = 600) -> None:
    start = date(2025, 1, 1)
    end = date(2026, 6, 30)
    path = DATA_DIR / "sample_customers.csv"

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["customer_id", "signup_date", "region", "signup_channel"])

        for i in range(1, customer_count + 1):
            customer_id = f"C{i:05d}"
            writer.writerow(
                [
                    customer_id,
                    random_date(start, end).isoformat(),
                    random.choice(REGIONS),
                    random.choice(CHANNELS),
                ]
            )


def write_orders(order_count: int = 5200, customer_count: int = 600) -> None:
    start = date(2025, 7, 1)
    end = date(2026, 6, 30)
    path = DATA_DIR / "sample_orders.csv"

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "order_id",
                "customer_id",
                "order_date",
                "category",
                "quantity",
                "unit_price",
                "discount_rate",
                "paid_amount",
                "order_status",
            ]
        )

        for i in range(1, order_count + 1):
            category = random.choice(list(CATEGORIES.keys()))
            low, high = CATEGORIES[category]
            quantity = random.choices([1, 2, 3, 4, 5], weights=[52, 24, 12, 8, 4])[0]
            unit_price = round(random.uniform(low, high), 2)
            discount_rate = random.choice([0, 0, 0.05, 0.08, 0.1, 0.15, 0.2])
            paid_amount = round(quantity * unit_price * (1 - discount_rate), 2)
            customer_id = f"C{random.randint(1, customer_count):05d}"
            writer.writerow(
                [
                    f"O{i:06d}",
                    customer_id,
                    random_date(start, end).isoformat(),
                    category,
                    quantity,
                    unit_price,
                    discount_rate,
                    paid_amount,
                    random.choice(STATUSES),
                ]
            )


def main() -> None:
    write_customers()
    write_orders()
    print(f"Generated synthetic data in {DATA_DIR}")


if __name__ == "__main__":
    main()

