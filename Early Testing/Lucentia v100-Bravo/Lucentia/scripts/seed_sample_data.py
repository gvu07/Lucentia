import argparse
import random
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

from app.database import SessionLocal
from app import models, insights
from app.auth import get_password_hash


SPENDING_PATTERNS = [
    {
        "name": "Whole Foods Market",
        "merchant": "Whole Foods",
        "category_primary": "FOOD_AND_DRINK",
        "category_detailed": "GROCERIES",
        "min_amount": 35,
        "max_amount": 140,
    },
    {
        "name": "Blue Bottle Coffee",
        "merchant": "Blue Bottle",
        "category_primary": "FOOD_AND_DRINK",
        "category_detailed": "COFFEE",
        "min_amount": 6,
        "max_amount": 18,
    },
    {
        "name": "Delta Airlines",
        "merchant": "Delta Air Lines",
        "category_primary": "TRAVEL",
        "category_detailed": "TRAVEL_FLIGHTS",
        "min_amount": 120,
        "max_amount": 450,
    },
    {
        "name": "Spotify Subscription",
        "merchant": "Spotify",
        "category_primary": "ENTERTAINMENT",
        "category_detailed": "STREAMING_SUBSCRIPTIONS",
        "min_amount": 10,
        "max_amount": 15,
    },
    {
        "name": "Uber Ride",
        "merchant": "Uber",
        "category_primary": "TRANSPORTATION",
        "category_detailed": "RIDESHARE",
        "min_amount": 12,
        "max_amount": 48,
    },
    {
        "name": "Amazon Marketplace",
        "merchant": "Amazon",
        "category_primary": "GENERAL_MERCHANDISE",
        "category_detailed": "GENERAL_MERCHANDISE_ONLINE",
        "min_amount": 20,
        "max_amount": 180,
    },
    {
        "name": "Equinox Membership",
        "merchant": "Equinox",
        "category_primary": "HEALTHCARE",
        "category_detailed": "GYM_FITNESS",
        "min_amount": 150,
        "max_amount": 250,
    },
]

SUBSCRIPTION_MERCHANTS = [
    {
        "name": "Spotify Premium",
        "merchant": "Spotify",
        "category_primary": "ENTERTAINMENT",
        "category_detailed": "STREAMING_SUBSCRIPTIONS",
        "amounts": [12.99, 12.99, 13.99],
    },
    {
        "name": "Adobe Creative Cloud",
        "merchant": "Adobe",
        "category_primary": "GENERAL_MERCHANDISE",
        "category_detailed": "SOFTWARE_SUBSCRIPTIONS",
        "amounts": [20.99, 20.99, 24.99],
    },
    {
        "name": "Netflix Subscription",
        "merchant": "Netflix",
        "category_primary": "ENTERTAINMENT",
        "category_detailed": "STREAMING_SUBSCRIPTIONS",
        "amounts": [15.49, 15.49, 15.49],
    },
    {
        "name": "Dollar Shave Club",
        "merchant": "Dollar Shave Club",
        "category_primary": "PERSONAL_CARE",
        "category_detailed": "PERSONAL_CARE_SUBSCRIPTIONS",
        "amounts": [45.0, 0, 0],  # Quarterly billing
    },
]

ATM_AND_FEE_EVENTS = [
    {
        "name": "ATM Fee",
        "merchant": "ATM Fee",
        "category_primary": "BANK_FEES",
        "category_detailed": "ATM_FEES",
        "amount": 4.0,
    },
    {
        "name": "Maintenance Fee",
        "merchant": "Bank Maintenance",
        "category_primary": "BANK_FEES",
        "category_detailed": "MAINTENANCE_FEES",
        "amount": 15.0,
    },
]

LOCAL_BUSINESSES = [
    {
        "name": "Farmers Market",
        "merchant": "Local Farmers Market",
        "category_primary": "FOOD_AND_DRINK",
        "category_detailed": "GROCERIES",
        "min_amount": 25,
        "max_amount": 80,
    },
    {
        "name": "Neighborhood Bakery",
        "merchant": "Sunrise Bakery",
        "category_primary": "FOOD_AND_DRINK",
        "category_detailed": "BAKERIES",
        "min_amount": 10,
        "max_amount": 30,
    },
]

RESTAURANT_SPOTS = [
    "Frita Batidos",
    "Ashley’s",
    "Sava’s",
    "Knight’s Downtown",
    "Gandy Dancer",
    "Black Pearl",
    "Slurping Turtle",
    "Aventura",
    "Pita Kabob Grill",
    "Mani Osteria and Bar",
    "Blue LLama Jazz Club & Restaurant",
    "The Chop House",
    "Madras Masala",
    "Metzger’s",
    "Taste Kitchen",
    "Echelon Kitchen & Bar",
    "Tomukun Noodle Bar",
    "The West End Grill",
    "Jerusalem Garden",
    "Zingerman’s Roadhouse",
    "Tomukun Korean BBQ",
    "Jamaican Jerk Pit",
    "HopCat",
    "Spencer",
    "Peridot",
]

INCOME_EVENTS = [
    {
        "name": "ACME Corp Payroll",
        "merchant": "ACME Corp",
        "category_primary": "INCOME",
        "category_detailed": "SALARY_WAGES",
        "amount": -2500,
    },
    {
        "name": "Side Hustle Payment",
        "merchant": "Upwork",
        "category_primary": "INCOME",
        "category_detailed": "FREELANCE_INCOME",
        "amount": -600,
    },
]


def ensure_user(session, email: str, password: str = "password123"):
    user = session.query(models.User).filter(models.User.email == email).first()
    if user:
        return user

    hashed = get_password_hash(password)
    user = models.User(email=email, hashed_password=hashed)
    session.add(user)
    session.commit()
    session.refresh(user)
    print(f"Created user {email} with default password {password}")
    return user


def ensure_account(session, user):
    account = (
        session.query(models.Account)
        .filter(models.Account.user_id == user.id)
        .order_by(models.Account.id.asc())
        .first()
    )
    if account:
        return account

    account = models.Account(
        user_id=user.id,
        plaid_account_id=f"sample-account-{user.id}",
        name="Sample Checking",
        official_name="Sample Checking Account",
        type="depository",
        subtype="checking",
        available_balance=Decimal("3000"),
        current_balance=Decimal("3000"),
        currency_code="USD",
        is_active=True,
    )
    session.add(account)
    session.commit()
    session.refresh(account)
    return account


def create_transactions(session, user, account, months=3, per_month=20):
    session.query(models.Transaction).filter(models.Transaction.user_id == user.id).delete()
    session.commit()

    today = datetime.utcnow().date()
    created = 0

    for month_offset in range(months):
        for _ in range(per_month):
            pattern = random.choice(SPENDING_PATTERNS)
            amount = Decimal(
                str(round(random.uniform(pattern["min_amount"], pattern["max_amount"]), 2))
            )
            days_ago = random.randint(month_offset * 30, (month_offset + 1) * 30 - 1)
            txn_date = datetime.combine(today - timedelta(days=days_ago), datetime.min.time())
            metadata = None
            if pattern["category_primary"] in {"TRANSPORTATION", "ENTERTAINMENT"} and random.random() < 0.3:
                metadata = "evening"

            transaction = models.Transaction(
                user_id=user.id,
                account_id=account.id,
                plaid_transaction_id=f"sample-spend-{user.id}-{created}",
                amount=amount,
                date=txn_date,
                name=pattern["name"],
                merchant_name=pattern["merchant"],
                category_primary=pattern["category_primary"],
                category_detailed=pattern["category_detailed"],
                payment_channel="card",
                payment_metadata=metadata,
                is_pending=False,
            )
            session.add(transaction)
            created += 1

        # Restaurant visits for richer dining insights
        restaurant_sample = random.sample(
            RESTAURANT_SPOTS,
            k=min(len(RESTAURANT_SPOTS), 10),
        )
        for idx, restaurant_name in enumerate(restaurant_sample):
            visits = random.randint(1, 3)
            for visit in range(visits):
                days_ago = random.randint(month_offset * 30, (month_offset + 1) * 30 - 1)
                txn_date = datetime.combine(today - timedelta(days=days_ago), datetime.min.time())
                amount = Decimal(str(round(random.uniform(18, 120), 2)))
                transaction = models.Transaction(
                    user_id=user.id,
                    account_id=account.id,
                    plaid_transaction_id=f"sample-restaurant-{user.id}-{month_offset}-{idx}-{visit}",
                    amount=amount,
                    date=txn_date,
                    name=restaurant_name,
                    merchant_name=restaurant_name,
                    category_primary="FOOD_AND_DRINK",
                    category_detailed="DINE_IN_RESTAURANT",
                    payment_channel="card",
                    is_pending=False,
                )
                session.add(transaction)
                created += 1

        # Local businesses to support sustainability insights
        for local in LOCAL_BUSINESSES:
            amount = Decimal(
                str(round(random.uniform(local["min_amount"], local["max_amount"]), 2))
            )
            txn_date = datetime.combine(
                today - timedelta(days=month_offset * 30 + random.randint(1, 10)),
                datetime.min.time()
            )
            transaction = models.Transaction(
                user_id=user.id,
                account_id=account.id,
                plaid_transaction_id=f"sample-local-{user.id}-{month_offset}-{local['merchant']}",
                amount=amount,
                date=txn_date,
                name=local["name"],
                merchant_name=local["merchant"],
                category_primary=local["category_primary"],
                category_detailed=local["category_detailed"],
                payment_channel="in_store",
                is_pending=False,
            )
            session.add(transaction)
            created += 1

        # Subscriptions
        for idx, sub in enumerate(SUBSCRIPTION_MERCHANTS):
            amount_series = sub["amounts"]
            amount_value = amount_series[month_offset % len(amount_series)]
            if amount_value == 0:
                continue
            txn_date = datetime.combine(
                today - timedelta(days=month_offset * 30 + 5 + idx),
                datetime.min.time()
            )
            transaction = models.Transaction(
                user_id=user.id,
                account_id=account.id,
                plaid_transaction_id=f"sample-sub-{user.id}-{month_offset}-{idx}",
                amount=Decimal(str(amount_value)),
                date=txn_date,
                name=sub["name"],
                merchant_name=sub["merchant"],
                category_primary=sub["category_primary"],
                category_detailed=sub["category_detailed"],
                payment_channel="subscription",
                is_pending=False,
            )
            session.add(transaction)
            created += 1

        # Add income once per month
        income = INCOME_EVENTS[month_offset % len(INCOME_EVENTS)]
        txn_date = datetime.combine(
            today - timedelta(days=month_offset * 30 + 2), datetime.min.time()
        )
        transaction = models.Transaction(
            user_id=user.id,
            account_id=account.id,
            plaid_transaction_id=f"sample-income-{user.id}-{month_offset}",
            amount=Decimal(str(income["amount"])),
            date=txn_date,
            name=income["name"],
            merchant_name=income["merchant"],
            category_primary=income["category_primary"],
            category_detailed=income["category_detailed"],
            payment_channel="direct_deposit",
            is_pending=False,
        )
        session.add(transaction)
        created += 1

        # Fees (ATM/maintenance)
        for fee in ATM_AND_FEE_EVENTS:
            if fee["category_detailed"] == "ATM_FEES":
                occurrences = random.randint(0, 3)
            else:
                occurrences = 1
            for occ in range(occurrences):
                txn_date = datetime.combine(
                    today - timedelta(days=month_offset * 30 + 10 + occ),
                    datetime.min.time()
                )
                transaction = models.Transaction(
                    user_id=user.id,
                    account_id=account.id,
                    plaid_transaction_id=f"sample-fee-{user.id}-{month_offset}-{fee['name']}-{occ}",
                    amount=Decimal(str(fee["amount"])),
                    date=txn_date,
                    name=fee["name"],
                    merchant_name=fee["merchant"],
                    category_primary=fee["category_primary"],
                    category_detailed=fee["category_detailed"],
                    payment_channel="bank_fee",
                    is_pending=False,
                )
                session.add(transaction)
                created += 1

    session.commit()
    print(f"Inserted {created} sample transactions for {user.email}")


def regenerate_insights(session, user):
    session.query(models.Insight).filter(models.Insight.user_id == user.id).delete()
    session.commit()

    engine = insights.InsightsEngine(session, user.id)
    engine.generate_all_insights()
    print(f"Regenerated insights for {user.email}")


def seed_user(email: str, months: int = 3, per_month: int = 20, create_if_missing: bool = False, password: str = "password123"):
    session = SessionLocal()
    try:
        user = session.query(models.User).filter(models.User.email == email).first()
        if not user:
            if not create_if_missing:
                print(f"No user found for email {email}")
                return
            user = ensure_user(session, email, password=password)

        account = ensure_account(session, user)
        create_transactions(session, user, account, months=months, per_month=per_month)
        regenerate_insights(session, user)
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(description="Seed sample financial data for a user.")
    parser.add_argument(
        "--email",
        default="cli_test@example.com",
        help="User email to seed (default: cli_test@example.com)",
    )
    parser.add_argument("--months", type=int, default=3, help="Number of months of data to generate")
    parser.add_argument("--per-month", type=int, default=20, help="Transactions per month")
    parser.add_argument("--create-if-missing", action="store_true", help="Create user automatically if missing")
    parser.add_argument("--password", default="password123", help="Password to use when auto-creating users")
    args = parser.parse_args()

    seed_user(
        email=args.email,
        months=args.months,
        per_month=args.per_month,
        create_if_missing=args.create_if_missing,
        password=args.password,
    )


if __name__ == "__main__":
    main()
