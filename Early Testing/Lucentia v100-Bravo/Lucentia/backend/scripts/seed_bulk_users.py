import argparse

from .seed_sample_data import seed_user


def main():
    parser = argparse.ArgumentParser(description="Seed multiple users with sample data.")
    parser.add_argument("--start", type=int, default=2, help="Starting user index (inclusive).")
    parser.add_argument("--end", type=int, default=19, help="Ending user index (inclusive).")
    parser.add_argument("--months", type=int, default=3, help="Months of data to generate per user.")
    parser.add_argument("--per-month", type=int, default=20, help="Transactions per month per user.")
    args = parser.parse_args()

    for i in range(args.start, args.end + 1):
        email = f"cli_test{i}@example.com"
        print(f"Seeding {email} ...")
        seed_user(
            email=email,
            months=args.months,
            per_month=args.per_month,
            create_if_missing=True,
            password="password123",
        )


if __name__ == "__main__":
    main()
