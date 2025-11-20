import sys
from datetime import datetime, timedelta
from decimal import Decimal
from itertools import count
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from app import models  # noqa: E402
from app.insights import InsightsEngine  # noqa: E402

_TXN_COUNTER = count(1)


def make_transaction(
    amount,
    *,
    date=None,
    days_ago=None,
    category="FOOD_AND_DRINK",
    category_detailed=None,
    merchant="Test Merchant",
    name=None,
    account_id=1,
):
    if date is None:
        reference = datetime.utcnow()
        delta_days = 0 if days_ago is None else days_ago
        date = reference - timedelta(days=delta_days)
    idx = next(_TXN_COUNTER)
    return models.Transaction(
        id=idx,
        user_id=1,
        account_id=account_id,
        plaid_transaction_id=f"test-{idx}",
        amount=Decimal(str(amount)),
        currency_code="USD",
        date=date,
        name=name or merchant,
        merchant_name=merchant,
        category_primary=category,
        category_detailed=category_detailed or category,
        category_confidence_level=None,
        payment_channel="card",
        payment_metadata=None,
        location_city=None,
        location_region=None,
        location_country=None,
        is_pending=False,
        is_recurring=False,
        created_at=date,
        updated_at=date,
    )


def build_engine(transactions):
    engine = InsightsEngine.__new__(InsightsEngine)
    engine.transactions = transactions
    engine.accounts = []
    engine.db = None
    engine.user_id = 1
    return engine


class InsightsEngineDetectorTests(unittest.TestCase):
    def test_burst_spending_detected(self):
        now = datetime.utcnow()
        txns = [
            make_transaction(32, date=now - timedelta(hours=idx * 8), merchant=f"Diner {idx}")
            for idx in range(6)
        ]
        engine = build_engine(txns)

        insights = engine._generate_spending_pattern_insights()
        families = {ins["family"]: ins for ins in insights}

        self.assertIn("burst_spending", families)
        self.assertIn("spike", families["burst_spending"]["description"])

    def test_merchant_switching_behavior(self):
        now = datetime.utcnow()
        transactions = []
        for offset in range(4):
            transactions.append(
                make_transaction(
                    18,
                    date=now - timedelta(days=35 + offset),
                    merchant="Sweetgreen",
                    category="FOOD_AND_DRINK",
                )
            )
        for offset in range(4):
            transactions.append(
                make_transaction(
                    17,
                    date=now - timedelta(days=offset * 2),
                    merchant="Panera",
                    category="FOOD_AND_DRINK",
                )
            )
        engine = build_engine(transactions)

        insights = engine._generate_spending_pattern_insights()
        families = {ins["family"]: ins for ins in insights}

        self.assertIn("merchant_switching", families)
        self.assertIn("Panera", families["merchant_switching"]["description"])

    def test_category_saturation_threshold(self):
        engine = build_engine([])
        current_start = engine._month_start(datetime.utcnow())
        transactions = []
        for day in range(4):
            transactions.append(
                make_transaction(
                    160,
                    date=current_start + timedelta(days=day),
                    category="FOOD_AND_DRINK",
                )
            )
        transactions.append(
            make_transaction(
                100,
                date=current_start + timedelta(days=1),
                category="GENERAL_MERCHANDISE",
            )
        )
        baseline_date = current_start - timedelta(days=20)
        transactions.append(
            make_transaction(
                200,
                date=baseline_date,
                category="FOOD_AND_DRINK",
            )
        )
        transactions.append(
            make_transaction(
                400,
                date=baseline_date,
                category="GENERAL_MERCHANDISE",
            )
        )
        engine = build_engine(transactions)

        insights = engine._generate_spending_pattern_insights()
        families = {ins["family"]: ins for ins in insights}

        self.assertIn("category_saturation", families)
        self.assertIn("Food And Drink", families["category_saturation"]["description"])

    def test_merchant_bundling_opportunity(self):
        now = datetime.utcnow()
        merchants = ["Local Beans", "Daily Grind", "Roastery Hub"]
        transactions = []
        for merchant in merchants:
            for visit in range(2):
                transactions.append(
                    make_transaction(
                        12 + visit,
                        date=now - timedelta(days=visit * 3),
                        merchant=merchant,
                        category="FOOD_AND_DRINK",
                    )
                )
        engine = build_engine(transactions)

        insights = engine._generate_merchant_insights()
        families = {ins["family"]: ins for ins in insights}

        self.assertIn("merchant_bundling", families)
        sample = families["merchant_bundling"]["data"].get("sample_merchants", [])
        self.assertGreaterEqual(len(sample), 2)

    def test_local_shop_loyalty_signal(self):
        now = datetime.utcnow()
        restaurants = ["Maple Cafe", "River Bistro"]
        transactions = []
        for merchant in restaurants:
            for visit in range(3):
                transactions.append(
                    make_transaction(
                        28 + visit,
                        date=now - timedelta(days=visit * 5),
                        merchant=merchant,
                        category="FOOD_AND_DRINK",
                        name=f"{merchant} Local",
                    )
                )
        transactions.append(
            make_transaction(
                75,
                date=now - timedelta(days=2),
                merchant="Supermarket",
                category="GROCERIES",
            )
        )
        engine = build_engine(transactions)

        insights = engine._generate_sustainability_insights()
        families = {ins["family"]: ins for ins in insights}

        self.assertIn("local_shop_loyalty", families)
        self.assertIn("Maple Cafe", families["local_shop_loyalty"]["data"]["merchants"])


if __name__ == "__main__":
    unittest.main()
