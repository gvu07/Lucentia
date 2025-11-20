from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict

from sqlalchemy.orm import Session

from . import models, insights, crud

DEMO_METADATA_MARKER = "demo_seed"

DEMO_SPENDING_EVENTS: List[Dict] = [
    {
        "name": "Mortgage Payment",
        "merchant": "Ann Arbor Mortgage",
        "amount": Decimal("1650.00"),
        "category_primary": "RENT_AND_UTILITIES",
        "category_detailed": "MORTGAGE",
        "day_offset": 3,
    },
    {
        "name": "Whole Foods Grocery",
        "merchant": "Whole Foods",
        "amount": Decimal("145.50"),
        "category_primary": "FOOD_AND_DRINK",
        "category_detailed": "GROCERIES",
        "day_offset": 5,
    },
    {
        "name": "Zingerman's Dinner",
        "merchant": "Zingerman's",
        "amount": Decimal("68.25"),
        "category_primary": "FOOD_AND_DRINK",
        "category_detailed": "DINE_IN_RESTAURANT",
        "day_offset": 9,
    },
    {
        "name": "DTE Energy",
        "merchant": "DTE Energy",
        "amount": Decimal("135.00"),
        "category_primary": "RENT_AND_UTILITIES",
        "category_detailed": "UTILITIES",
        "day_offset": 11,
    },
    {
        "name": "Comcast Internet",
        "merchant": "Comcast",
        "amount": Decimal("95.00"),
        "category_primary": "RENT_AND_UTILITIES",
        "category_detailed": "UTILITIES",
        "day_offset": 13,
    },
    {
        "name": "RoosRoast Coffee",
        "merchant": "RoosRoast",
        "amount": Decimal("18.00"),
        "category_primary": "FOOD_AND_DRINK",
        "category_detailed": "COFFEE",
        "day_offset": 16,
    },
    {
        "name": "Peloton Subscription",
        "merchant": "Peloton",
        "amount": Decimal("44.00"),
        "category_primary": "HEALTHCARE",
        "category_detailed": "GYM_FITNESS",
        "day_offset": 20,
    },
    {
        "name": "Toyota Auto Payment",
        "merchant": "Toyota Financial",
        "amount": Decimal("410.00"),
        "category_primary": "TRANSPORTATION",
        "category_detailed": "AUTO_FINANCE",
        "day_offset": 22,
    },
    {
        "name": "State Street Boutique",
        "merchant": "State Street Boutique",
        "amount": Decimal("125.00"),
        "category_primary": "GENERAL_MERCHANDISE",
        "category_detailed": "CLOTHING_STORES",
        "day_offset": 25,
    },
]

DEMO_INCOME_EVENTS: List[Dict] = [
    {
        "name": "ACME Corp Payroll",
        "merchant": "ACME Corp",
        "amount": Decimal("3600.00"),
        "category_primary": "INCOME",
        "category_detailed": "SALARY_WAGES",
        "day_offset": 1,
    },
    {
        "name": "Consulting Invoice",
        "merchant": "Freelance Consulting",
        "amount": Decimal("550.00"),
        "category_primary": "INCOME",
        "category_detailed": "FREELANCE_INCOME",
        "day_offset": 10,
    },
]


def _ensure_demo_account(db: Session, user: models.User) -> models.Account:
    account = (
        db.query(models.Account)
        .filter(models.Account.user_id == user.id)
        .order_by(models.Account.id.asc())
        .first()
    )
    if account:
        return account

    account = models.Account(
        user_id=user.id,
        plaid_account_id=f"demo-account-{user.id}",
        name="Demo Checking",
        official_name="Demo Checking Account",
        type="depository",
        subtype="checking",
        available_balance=Decimal("4800.00"),
        current_balance=Decimal("4800.00"),
        currency_code="USD",
        is_active=True,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def seed_demo_dataset(db: Session, user_id: int) -> None:
    user = crud.get_user(db, user_id)
    if not user:
        return

    account = _ensure_demo_account(db, user)

    db.query(models.Transaction).filter(models.Transaction.user_id == user_id).delete()
    db.query(models.Insight).filter(models.Insight.user_id == user_id).delete()
    db.commit()

    today = datetime.utcnow().date()
    for month_offset in range(3):
        base = today - timedelta(days=month_offset * 30)
        for income in DEMO_INCOME_EVENTS:
            txn_date = datetime.combine(
                base - timedelta(days=income["day_offset"]), datetime.min.time()
            )
            transaction = models.Transaction(
                user_id=user.id,
                account_id=account.id,
                plaid_transaction_id=f"demo-income-{user.id}-{month_offset}-{income['name']}",
                amount=-income["amount"],
                currency_code="USD",
                date=txn_date,
                name=income["name"],
                merchant_name=income["merchant"],
                category_primary=income["category_primary"],
                category_detailed=income["category_detailed"],
                payment_channel="direct_deposit",
                payment_metadata=DEMO_METADATA_MARKER,
                is_pending=False,
            )
            db.add(transaction)

        for spend in DEMO_SPENDING_EVENTS:
            txn_date = datetime.combine(
                base - timedelta(days=spend["day_offset"]), datetime.min.time()
            )
            transaction = models.Transaction(
                user_id=user.id,
                account_id=account.id,
                plaid_transaction_id=f"demo-spend-{user.id}-{month_offset}-{spend['name']}",
                amount=spend["amount"],
                currency_code="USD",
                date=txn_date,
                name=spend["name"],
                merchant_name=spend["merchant"],
                category_primary=spend["category_primary"],
                category_detailed=spend["category_detailed"],
                payment_channel="card",
                payment_metadata=DEMO_METADATA_MARKER,
                is_pending=False,
            )
            db.add(transaction)

    db.commit()

    engine = insights.InsightsEngine(db, user_id)
    engine.generate_all_insights()


def clear_demo_data(db: Session, user_id: int) -> None:
    db.query(models.Transaction).filter(
        models.Transaction.user_id == user_id,
        models.Transaction.payment_metadata == DEMO_METADATA_MARKER,
    ).delete(synchronize_session=False)
    db.query(models.Account).filter(
        models.Account.user_id == user_id,
        models.Account.plaid_account_id.like("demo-account-%"),
    ).delete(synchronize_session=False)
    db.query(models.Insight).filter(models.Insight.user_id == user_id).delete()
    db.commit()
