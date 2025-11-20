from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional
import json
import math

from sqlalchemy.orm import Session

from . import crud, models, schemas
from .insight_registry import get_family_meta


class InsightsEngine:
    DINING_CATEGORIES = {
        "FOOD_AND_DRINK",
        "RESTAURANTS",
        "BARS",
        "FOOD_DELIVERY",
        "COFFEE",
    }
    GROCERY_CATEGORIES = {"GROCERIES", "SUPERMARKETS"}
    DELIVERY_KEYWORDS = ["uber eats", "doordash", "grubhub", "postmates", "delivery"]
    SUBSCRIPTION_KEYWORDS = [
        "subscription",
        "netflix",
        "spotify",
        "hulu",
        "adobe",
        "prime",
        "membership",
        "cloud",
        "shave",
    ]
    RIDESHARE_KEYWORDS = ["uber", "lyft"]
    LOCAL_KEYWORDS = [
        "local",
        "market",
        "cafe",
        "bakery",
        "farmers market",
        "co-op",
        "kitchen",
        "bistro",
        "cantina",
        "brew",
        "taproom",
        "eatery",
        "collective",
        "roastery",
        "diner",
    ]
    FITNESS_KEYWORDS = ["gym", "fitness", "pilates", "yoga", "cycle", "boxing", "studio", "training"]
    FITNESS_CATEGORIES = {
        "GYM",
        "GYMS",
        "GYMS_AND_FITNESS",
        "SPORTS_AND_RECREATION",
        "FITNESS",
        "HEALTH_AND_FITNESS",
    }
    LOW_WASTE_KEYWORDS = [
        "thrift",
        "consignment",
        "secondhand",
        "resale",
        "reuse",
        "vintage",
        "goodwill",
        "salvation army",
        "plato",
        "buffalo exchange",
    ]
    AIRLINE_KEYWORDS = [
        "airlines",
        "delta",
        "united",
        "american airlines",
        "southwest",
        "jetblue",
        "alaska airlines",
        "frontier",
        "spirit airlines",
        "air canada",
    ]
    LOW_WASTE_CATEGORIES = {"SECOND_HAND", "CHARITY", "USED_MERCHANDISE"}
    TRAVEL_CATEGORIES = {"TRAVEL", "AIRLINES", "AIR_TRAVEL", "AIRLINE", "LODGING", "HOTELS"}
    PRIORITY_OVERRIDES = {
        "cash_buffer": "high",
        "balance_warning": "high",
        "payment_method_optimization": "high",
        "category_subscription_opportunity": "high",
        "category_spike": "high",
        "duplicate_services": "medium",
        "duplicate_subscription": "medium",
        "fee_detection": "medium",
        "category_saturation": "medium",
        "category_volatility": "medium",
        "cost_drift": "medium",
        "burst_spending": "medium",
        "air_travel_footprint": "medium",
        "merchant_loyalty": "medium",
        "merchant_bundling": "medium",
        "high_frequency_small": "medium",
        "cross_user_affinity": "medium",
        "restaurant_comeback": "medium",
        "favorite_restaurant_push": "medium",
    }
    DUPLICATE_SERVICE_KEYWORDS = {
        "cloud_storage": {
            "label": "cloud storage",
            "keywords": [
                "icloud",
                "google storage",
                "google drive",
                "dropbox",
                "onedrive",
                "box.com",
                "pcloud",
            ],
        },
        "productivity_suite": {
            "label": "productivity tools",
            "keywords": [
                "microsoft 365",
                "office 365",
                "notion",
                "evernote",
                "asana",
                "todoist",
            ],
        },
        "video_streaming": {
            "label": "video streaming",
            "keywords": ["netflix", "hulu", "disney+", "max", "prime video", "apple tv"],
        },
    }
    CATEGORY_BUCKET_LABELS = {
        "DINING": "restaurants and dining",
        "GROCERY": "grocery stores",
        "TRANSPORT": "transportation and rideshare",
        "TRAVEL": "travel",
        "FITNESS": "fitness",
        "RETAIL": "retail and general merchandise",
        "SUBSCRIPTION": "subscriptions and streaming",
    }
    SMALL_PURCHASE_THRESHOLD = Decimal("10")

    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
        self.transactions: List[models.Transaction] = []
        self.accounts: List[models.Account] = []
        self.primary_currency: str = "USD"
        self._load_data()

    def _load_data(self):
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=180)
        self.primary_currency = crud.get_primary_currency_for_user(self.db, self.user_id)
        fetched = crud.get_transactions_by_user(
            self.db, self.user_id, limit=10000, start_date=start_date, end_date=end_date
        )
        self.transactions = [
            txn
            for txn in fetched
            if (txn.currency_code or "USD") == self.primary_currency and not txn.is_pending
        ]
        self.accounts = crud.get_accounts_by_user(self.db, self.user_id)

    def _normalize_category(self, category: Optional[str]) -> Optional[str]:
        if not category:
            return None
        return str(category).upper().replace(" ", "_")

    def _format_category_label(self, category: Optional[str]) -> str:
        if not category:
            return "General"
        return self._normalize_category(category).replace("_", " ").title()

    def _category_bucket(self, category: Optional[str], merchant_name: Optional[str] = None) -> Optional[str]:
        normalized = self._normalize_category(category)
        name = (merchant_name or "").lower()

        def name_has(*keywords: str) -> bool:
            return any(k in name for k in keywords if k)

        if normalized in self.DINING_CATEGORIES or name_has("restaurant", "cafe", "pizza", "bbq", "grill", "diner"):
            return "DINING"
        if normalized in self.GROCERY_CATEGORIES or name_has("market", "grocer", "grocery", "supermarket", "whole foods"):
            return "GROCERY"
        if normalized in self.TRAVEL_CATEGORIES or name_has("hotel", "inn", "airlines", "airport"):
            return "TRAVEL"
        if normalized in self.FITNESS_CATEGORIES or self._matches_keywords(name, self.FITNESS_KEYWORDS):
            return "FITNESS"
        if normalized and "TRANSPORT" in normalized:
            return "TRANSPORT"
        if self._matches_keywords(name, self.RIDESHARE_KEYWORDS):
            return "TRANSPORT"
        if normalized == "GENERAL_MERCHANDISE" or name_has("shop", "outlet", "store", "mall"):
            return "RETAIL"
        if self._matches_keywords(name, self.SUBSCRIPTION_KEYWORDS):
            return "SUBSCRIPTION"
        return None

    def _is_spending(self, transaction: models.Transaction) -> bool:
        return transaction.amount is not None and transaction.amount > 0

    def _positive_sum(self, txns: List[models.Transaction]) -> Decimal:
        return sum(t.amount for t in txns if self._is_spending(t))

    def _normalize_merchant_label(self, transaction: models.Transaction) -> str:
        return (transaction.merchant_name or transaction.name or "").strip()

    def _matches_keywords(self, value: Optional[str], keywords: List[str]) -> bool:
        if not value:
            return False
        lower_value = value.lower()
        return any(keyword in lower_value for keyword in keywords)

    def _is_local_transaction(self, transaction: models.Transaction) -> bool:
        if not self._is_spending(transaction):
            return False
        name = self._normalize_merchant_label(transaction).lower()
        city = (transaction.location_city or "").lower()
        return self._matches_keywords(name, self.LOCAL_KEYWORDS) or (city and city in name)

    def _month_start(self, dt: datetime) -> datetime:
        return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    def _create_insight(
        self,
        family_key: str,
        *,
        title: Optional[str] = None,
        description: Optional[str] = None,
        priority: str = "medium",
        data: Optional[Dict[str, Any]] = None,
        context: Optional[str] = None,
    ) -> Dict[str, Any]:
        family_meta = get_family_meta(family_key)
        payload = data.copy() if data else {}
        payload.setdefault(
            "comparison_context",
            context or "Based on the last 90 days of activity.",
        )

        def _rank(value: str) -> int:
            normalized = (value or "medium").lower()
            if normalized == "high":
                return 0
            if normalized == "medium":
                return 1
            return 2

        override = self.PRIORITY_OVERRIDES.get(family_key)
        normalized_priority = priority
        if override and _rank(override) < _rank(priority):
            normalized_priority = override

        return {
            "domain": family_meta["domain"],
            "family": family_key,
            "title": title or family_meta["name"],
            "description": description or family_meta.get("description", ""),
            "priority": normalized_priority,
            "data": payload,
        }

    def generate_all_insights(self) -> schemas.InsightsResponse:
        crud.delete_insights_by_user(self.db, self.user_id)
        self._load_data()

        if not self.transactions:
            return crud.get_all_insights_by_user(self.db, self.user_id)

        generated: List[Dict[str, Any]] = []
        generated.extend(self._generate_dining_insights())
        generated.extend(self._generate_spending_pattern_insights())
        generated.extend(self._generate_financial_health_insights())
        generated.extend(self._generate_merchant_insights())
        generated.extend(self._generate_behavioral_insights())
        generated.extend(self._generate_transportation_insights())
        generated.extend(self._generate_cross_user_affinity_insights())
        generated.extend(self._generate_sustainability_insights())
        generated.extend(self._generate_consumption_insights())
        generated.extend(self._generate_income_insights())
        generated.extend(self._generate_goal_insights())

        for insight in generated:
            insight_data = schemas.InsightCreate(
                user_id=self.user_id,
                domain=insight["domain"],
                family=insight["family"],
                title=insight["title"],
                description=insight["description"],
                data=json.dumps(insight.get("data", {})),
                priority=insight.get("priority", "medium"),
            )
            crud.create_insight(self.db, insight_data)

        return crud.get_all_insights_by_user(self.db, self.user_id)

    # ----- Dining & Spending Patterns -----
    def _generate_dining_insights(self) -> List[Dict[str, Any]]:
        insights: List[Dict[str, Any]] = []

        dining_transactions = [
            t
            for t in self.transactions
            if self._normalize_category(t.category_primary) in self.DINING_CATEGORIES
        ]
        if not dining_transactions:
            return insights

        current_month_start = datetime.utcnow().replace(day=1)
        this_month_dining = sum(
            t.amount
            for t in dining_transactions
            if self._is_spending(t) and t.date >= current_month_start
        )
        three_months_ago = datetime.utcnow() - timedelta(days=90)
        monthly_totals: Dict[str, Decimal] = {}
        for t in dining_transactions:
            if t.date >= three_months_ago and self._is_spending(t):
                key = t.date.strftime("%Y-%m")
                monthly_totals[key] = monthly_totals.get(key, Decimal("0")) + t.amount
        if len(monthly_totals) > 1:
            avg = sum(monthly_totals.values()) / len(monthly_totals)
            if avg > 0 and this_month_dining > avg * Decimal("1.3"):
                pct = ((this_month_dining - avg) / avg) * 100
                insights.append(
                    self._create_insight(
                        "category_spike",
                        title="Dining Spending Increase",
                        description=f"Dining is up {pct:.0f}% vs your 3‑month average.",
                        priority="medium",
                        data={
                            "this_month": float(this_month_dining),
                            "average": float(avg),
                            "increase_percentage": float(pct),
                        },
                        context="Current month compared to previous three-month rolling average.",
                    )
                )

        delivery_total = sum(
            t.amount
            for t in self.transactions
            if self._is_spending(t)
            and (
                self._normalize_category(t.category_detailed) == "FOOD_DELIVERY"
                or any(keyword in (t.name or "").lower() for keyword in self.DELIVERY_KEYWORDS)
            )
        )
        grocery_total = sum(
            t.amount
            for t in self.transactions
            if self._is_spending(t)
            and self._normalize_category(t.category_detailed) in self.GROCERY_CATEGORIES
        )
        if grocery_total > 0 and delivery_total > grocery_total * Decimal("1.5"):
            ratio = (delivery_total / grocery_total) * 100
            insights.append(
                self._create_insight(
                    "delivery_vs_grocery",
                    description="Food delivery outpaces grocery spending — meal planning could lower costs.",
                    priority="medium",
                    data={
                        "delivery_spending": float(delivery_total),
                        "grocery_spending": float(grocery_total),
                        "percentage": float(ratio),
                    },
                    context="Comparison over the last 30 days.",
                )
            )

        coffee_runs = [
            t
            for t in dining_transactions
            if "coffee" in (t.name or "").lower()
            or self._normalize_category(t.category_detailed) == "COFFEE"
        ]
        if len(coffee_runs) >= 12:
            insights.append(
                self._create_insight(
                    "habit_frequency",
                    title="Daily Coffee Habit",
                    description=f"{len(coffee_runs)} coffee purchases logged recently — a rewards program could cut costs.",
                    priority="low",
                    data={
                        "transactions": len(coffee_runs),
                        "total_spent": float(self._positive_sum(coffee_runs)),
                    },
                    context="Based on the past 90 days of coffee-related transactions.",
                )
            )

        restaurant_stats: Dict[str, Dict[str, Any]] = {}
        for t in dining_transactions:
            name = t.merchant_name or t.name
            if not name:
                continue
            stats = restaurant_stats.setdefault(
                name,
                {
                    "count": 0,
                    "total": Decimal("0"),
                    "last_visit": t.date,
                },
            )
            stats["count"] += 1
            if self._is_spending(t):
                stats["total"] += t.amount
            if t.date > stats["last_visit"]:
                stats["last_visit"] = t.date

        now = datetime.utcnow()
        for name, stats in restaurant_stats.items():
            if stats["count"] >= 3 and stats["total"] > Decimal("90"):
                insights.append(
                    self._create_insight(
                        "favorite_merchants",
                        title=f"{name} is a Favorite",
                        description=f"You visited {name} {stats['count']} times recently — check their loyalty perks.",
                        priority="low",
                        data={
                            "visits": stats["count"],
                            "total_spent": float(stats["total"]),
                        },
                        context="Calculated from the last 90 days of visits.",
                    )
                )

            days_since = (now - stats["last_visit"]).days
            if stats["count"] >= 2 and days_since >= 30:
                insights.append(
                    self._create_insight(
                        "lapsed_favorites",
                        title=f"Visit {name} Again?",
                        description=f"It’s been {days_since} days since your last visit to {name}.",
                        priority="low",
                        data={
                            "days_since_visit": days_since,
                            "total_visits": stats["count"],
                        },
                        context="Based on visit history within the last 90 days.",
                    )
                )

            if stats["count"] >= 1 and days_since >= 21:
                insights.append(
                    self._create_insight(
                        "restaurant_comeback",
                        title=f"Return to {name}",
                        description=f"It’s been {days_since} days since you visited {name}. Plan a visit?",
                        priority="medium",
                        data={
                            "days_since_visit": days_since,
                            "recent_visits": stats["count"],
                        },
                        context="Recent dining history across the last 90 days.",
                    )
                )

            if stats["count"] >= 3 and days_since <= 45:
                insights.append(
                    self._create_insight(
                        "favorite_restaurant_push",
                        title=f"Make the Most of {name}",
                        description=f"You’ve visited {name} {stats['count']} times recently. Consider booking again or using loyalty perks.",
                        priority="medium",
                        data={
                            "recent_visits": stats["count"],
                            "recent_spend": float(stats["total"]),
                            "days_since_last": days_since,
                        },
                        context="Based on dining frequency and recent spend.",
                    )
                )

        return insights

    # ----- Financial Health & Optimization -----
    def _generate_financial_health_insights(self) -> List[Dict[str, Any]]:
        insights: List[Dict[str, Any]] = []

        subscription_map: Dict[str, List[models.Transaction]] = defaultdict(list)
        for t in self.transactions:
            if not self._is_spending(t):
                continue
            merchant = (t.merchant_name or t.name or "").lower()
            if any(keyword in merchant for keyword in self.SUBSCRIPTION_KEYWORDS):
                subscription_map[merchant].append(t)

        subscription_transactions = [txn for txns in subscription_map.values() for txn in txns]
        if subscription_transactions:
            total_subscriptions = self._positive_sum(subscription_transactions)
            unique_merchants = len(subscription_map)
            if total_subscriptions > 400 or unique_merchants >= 5:
                insights.append(
                    self._create_insight(
                        "subscription_volume",
                        title="Heavy Subscription Load",
                        description=f"{unique_merchants} recurring merchants billed you this quarter — review for overlaps.",
                        priority="medium",
                        data={
                            "merchant_count": unique_merchants,
                            "transaction_count": len(subscription_transactions),
                            "total_spent": float(total_subscriptions),
                        },
                        context="Evaluated over the last 90 days of subscription charges.",
                    )
                )
            for merchant, txns in subscription_map.items():
                if len(txns) < 2:
                    continue
                txns.sort(key=lambda t: t.date)
                latest, previous = txns[-1], txns[-2]
                if previous.amount > 0:
                    change_pct = ((latest.amount - previous.amount) / previous.amount) * 100
                    if abs(change_pct) >= 10:
                        insights.append(
                            self._create_insight(
                                "subscription_price_change",
                                title=f"{merchant.title()} Price Change",
                                description=f"{merchant.title()} changed from ${previous.amount:.2f} to ${latest.amount:.2f}.",
                                priority="medium",
                                data={
                                    "merchant": merchant.title(),
                                    "previous_amount": float(previous.amount),
                                    "current_amount": float(latest.amount),
                                    "percentage_change": float(change_pct),
                                },
                                context="Latest billing cycle compared to the previous charge.",
                            )
                        )

        total_balance = sum((acc.current_balance or 0) for acc in self.accounts)
        if self.accounts and total_balance > 5000:
            insights.append(
                self._create_insight(
                    "cash_buffer",
                    title="Cash Drag in Checking",
                    description="There is sizable idle cash in checking — moving a portion to high-yield savings could earn more.",
                    priority="medium",
                    data={
                        "total_balance": float(total_balance),
                        "accounts": len(self.accounts),
                    },
                    context="Snapshot of current account balances.",
                )
            )
        if total_balance < 200:
            insights.append(
                self._create_insight(
                    "balance_warning",
                    title="Low Account Balance",
                    description="Balances are low — consider keeping a small buffer to avoid overdrafts.",
                    priority="high",
                    data={"current_balance": float(total_balance)},
                    context="Snapshot of current account balances.",
                )
            )

        atm_fees = [
            t
            for t in self.transactions
            if self._is_spending(t)
            and self._normalize_category(t.category_detailed) == "ATM_FEES"
        ]
        if atm_fees and len(atm_fees) >= 3:
            insights.append(
                self._create_insight(
                    "fee_detection",
                    title="ATM Fee Drain",
                    description="Multiple ATM fees detected — check if your bank offers fee-free networks.",
                    priority="low",
                    data={
                        "transactions": len(atm_fees),
                        "total_fees": float(self._positive_sum(atm_fees)),
                    },
                    context="Fees detected over the last 90 days.",
                )
            )

        return insights

    def _generate_spending_pattern_insights(self) -> List[Dict[str, Any]]:
        insights: List[Dict[str, Any]] = []
        if not self.transactions:
            return insights

        now = datetime.utcnow()

        # Burst spending detection (dining focus)
        dining_txns = sorted(
            [
                t
                for t in self.transactions
                if self._is_spending(t)
                and self._normalize_category(t.category_primary) in self.DINING_CATEGORIES
            ],
            key=lambda t: t.date,
        )
        if len(dining_txns) >= 5:
            left = 0
            best_window: Optional[Dict[str, Any]] = None
            for right, txn in enumerate(dining_txns):
                while dining_txns[right].date - dining_txns[left].date > timedelta(days=3):
                    left += 1
                window_count = right - left + 1
                if window_count >= 5:
                    window_txns = dining_txns[left : right + 1]
                    window_total = sum(t.amount for t in window_txns)
                    if window_total < Decimal("50"):
                        continue
                    window_start = dining_txns[left].date
                    window_end = dining_txns[right].date
                    if not best_window or window_count > best_window["count"] or (
                        window_count == best_window["count"]
                        and window_total > best_window["total"]
                    ):
                        best_window = {
                            "count": window_count,
                            "total": window_total,
                            "start": window_start,
                            "end": window_end,
                        }
            if best_window:
                span_days = max(1, (best_window["end"] - best_window["start"]).days + 1)
                insights.append(
                    self._create_insight(
                        "burst_spending",
                        title="Burst of Dining Activity",
                        description=f"You had a {span_days}-day spike with {best_window['count']} dining purchases — possibly a special occasion or social streak.",
                        priority="medium",
                        data={
                            "transaction_count": best_window["count"],
                            "total_spent": float(best_window["total"]),
                            "window_start": best_window["start"].date().isoformat(),
                            "window_end": best_window["end"].date().isoformat(),
                        },
                        context="Detected within a rolling 3-day window.",
                    )
                )

        # Merchant switching and cost drift leverage 60-day window stats
        current_start = now - timedelta(days=30)
        previous_start = now - timedelta(days=60)
        merchant_stats: Dict[str, Dict[str, Any]] = {}
        for t in self.transactions:
            if not self._is_spending(t) or not t.merchant_name or t.date < previous_start:
                continue
            category = self._normalize_category(t.category_primary)
            stats = merchant_stats.setdefault(
                t.merchant_name,
                {
                    "category": category,
                    "current_count": 0,
                    "current_amount": Decimal("0"),
                    "previous_count": 0,
                    "previous_amount": Decimal("0"),
                },
            )
            if not stats["category"] and category:
                stats["category"] = category
            if t.date >= current_start:
                stats["current_count"] += 1
                stats["current_amount"] += t.amount
            else:
                stats["previous_count"] += 1
                stats["previous_amount"] += t.amount

        # Merchant switching behavior
        category_lapsed: Dict[str, Dict[str, Any]] = {}
        for merchant, stats in merchant_stats.items():
            category = stats["category"]
            if (
                category
                and stats["previous_count"] >= 3
                and stats["current_count"] == 0
            ):
                existing = category_lapsed.get(category)
                if not existing or stats["previous_count"] > existing["previous_count"]:
                    category_lapsed[category] = {
                        "merchant": merchant,
                        "previous_count": stats["previous_count"],
                    }

        for merchant, stats in merchant_stats.items():
            category = stats["category"]
            if (
                not category
                or stats["current_count"] < 3
                or stats["previous_count"] > 1
                or category not in category_lapsed
            ):
                continue
            prior = category_lapsed[category]
            if prior["merchant"] == merchant:
                continue
            category_label = self._format_category_label(category)
            insights.append(
                self._create_insight(
                    "merchant_switching",
                    title=f"Switched {category_label} Spot",
                    description=f"You’ve recently switched from {prior['merchant']} to {merchant} for {category_label.lower()} purchases — {stats['current_count']} visits vs {prior['previous_count']} last month.",
                    priority="medium",
                    data={
                        "new_merchant": merchant,
                        "old_merchant": prior["merchant"],
                        "new_visits": stats["current_count"],
                        "old_visits": prior["previous_count"],
                        "category": category_label,
                    },
                    context="Comparing the last 30 days to the prior 30-day period.",
                )
            )
            break

        # Cost drift detection
        drift_candidates: List[Dict[str, Any]] = []
        for merchant, stats in merchant_stats.items():
            if stats["current_count"] < 2 or stats["previous_count"] < 2:
                continue
            previous_avg = stats["previous_amount"] / stats["previous_count"]
            current_avg = stats["current_amount"] / stats["current_count"]
            if previous_avg > 0 and current_avg >= previous_avg * Decimal("1.15"):
                drift_candidates.append(
                    {
                        "merchant": merchant,
                        "previous_avg": previous_avg,
                        "current_avg": current_avg,
                        "growth": (current_avg - previous_avg) / previous_avg,
                    }
                )

        drift_candidates.sort(key=lambda item: item["growth"], reverse=True)
        for candidate in drift_candidates[:2]:
            insights.append(
                self._create_insight(
                    "cost_drift",
                    title=f"Rising Spend at {candidate['merchant']}",
                    description=f"Your average spend at {candidate['merchant']} rose from ${candidate['previous_avg']:.2f} to ${candidate['current_avg']:.2f} over 60 days.",
                    priority="medium",
                    data={
                        "merchant": candidate["merchant"],
                        "previous_average": float(candidate["previous_avg"]),
                        "current_average": float(candidate["current_avg"]),
                        "change_percentage": round(float(candidate["growth"]) * 100, 1),
                    },
                    context="Comparison between the last and prior 30-day windows.",
                )
            )

        # Category saturation (current month share vs prior baseline)
        current_month_start = self._month_start(now)
        baseline_start = current_month_start - timedelta(days=60)
        current_totals: Dict[str, Decimal] = defaultdict(Decimal)
        baseline_totals: Dict[str, Decimal] = defaultdict(Decimal)
        current_total = Decimal("0")
        baseline_total = Decimal("0")

        for t in self.transactions:
            if not self._is_spending(t):
                continue
            category = self._normalize_category(t.category_primary) or "GENERAL"
            if t.date >= current_month_start:
                current_totals[category] += t.amount
                current_total += t.amount
            elif t.date >= baseline_start:
                baseline_totals[category] += t.amount
                baseline_total += t.amount

        if current_total > 0:
            for category, amount in current_totals.items():
                share = amount / current_total
                baseline_amount = baseline_totals.get(category, Decimal("0"))
                baseline_share = (
                    baseline_amount / baseline_total if baseline_total > 0 else Decimal("0")
                )
                if (
                    amount >= current_total * Decimal("0.3")
                    and share - baseline_share >= Decimal("0.1")
                    and amount > Decimal("150")
                ):
                    category_label = self._format_category_label(category)
                    insights.append(
                        self._create_insight(
                            "category_saturation",
                            title=f"{category_label} Dominates Spending",
                            description=f"{category_label} made up {share * 100:.0f}% of your spending this month — well above the usual {baseline_share * 100:.0f}%.",
                            priority="medium",
                            data={
                                "category": category_label,
                                "current_share": round(float(share * 100), 1),
                                "baseline_share": round(float(baseline_share * 100), 1),
                                "current_amount": float(amount),
                            },
                            context="Current month compared to the prior 60 days.",
                        )
                    )

        # Category volatility (month-to-month variability)
        volatility_cutoff = now - timedelta(days=150)
        monthly_category_totals: Dict[str, Dict[str, Decimal]] = defaultdict(
            lambda: defaultdict(Decimal)
        )
        for t in self.transactions:
            if not self._is_spending(t) or t.date < volatility_cutoff:
                continue
            category = self._normalize_category(t.category_primary) or "GENERAL"
            month_key = t.date.strftime("%Y-%m")
            monthly_category_totals[category][month_key] += t.amount

        for category, month_values in monthly_category_totals.items():
            amounts = [float(value) for value in month_values.values() if value > 0]
            if len(amounts) < 3:
                continue
            mean_value = sum(amounts) / len(amounts)
            if mean_value == 0:
                continue
            variance = sum((value - mean_value) ** 2 for value in amounts) / len(amounts)
            std_dev = math.sqrt(variance)
            if std_dev / mean_value >= 0.6 and max(amounts) - min(amounts) >= 100:
                category_label = self._format_category_label(category)
                insights.append(
                    self._create_insight(
                        "category_volatility",
                        title=f"Volatile {category_label} Spending",
                        description=f"Your spending on {category_label} swings widely month-to-month (from ${min(amounts):.0f} to ${max(amounts):.0f}).",
                        priority="low",
                        data={
                            "category": category_label,
                            "standard_deviation": round(std_dev, 2),
                            "average": round(mean_value, 2),
                        },
                        context="Evaluated across roughly the last five months.",
                    )
                )

        # Consistency score (overall monthly stability)
        monthly_totals: Dict[str, Decimal] = defaultdict(Decimal)
        for t in self.transactions:
            if self._is_spending(t):
                month_key = t.date.strftime("%Y-%m")
                monthly_totals[month_key] += t.amount

        monthly_amounts = [float(value) for value in monthly_totals.values() if value > 0]
        if len(monthly_amounts) >= 3:
            mean_total = sum(monthly_amounts) / len(monthly_amounts)
            variance = (
                sum((value - mean_total) ** 2 for value in monthly_amounts) / len(monthly_amounts)
                if mean_total > 0
                else 0
            )
            std_total = math.sqrt(variance)
            volatility = min(1.0, std_total / mean_total) if mean_total > 0 else 1.0
            score = round((1 - volatility) * 100)
            insights.append(
                self._create_insight(
                    "consistency_score",
                    title="Consistency Score",
                    description=f"Your overall spending pattern is {score}% consistent month-to-month.",
                    priority="low",
                    data={
                        "score": score,
                        "average_monthly_spend": round(mean_total, 2),
                    },
                    context="Calculated across recent months of activity.",
                )
            )

        return insights

    def _generate_merchant_insights(self) -> List[Dict[str, Any]]:
        insights: List[Dict[str, Any]] = []
        merchant_spending: Dict[str, Decimal] = {}
        category_history: Dict[str, List[Decimal]] = defaultdict(list)

        # Build per-category monthly history for later context (e.g., electronics spikes)
        category_monthly_totals: Dict[str, Dict[str, Decimal]] = defaultdict(lambda: defaultdict(Decimal))
        for t in self.transactions:
            if not self._is_spending(t):
                continue
            category = self._normalize_category(t.category_primary) or "UNCATEGORIZED"
            month_key = t.date.strftime("%Y-%m")
            category_monthly_totals[category][month_key] += t.amount

        for category, month_map in category_monthly_totals.items():
            ordered = [amount for _, amount in sorted(month_map.items())]
            category_history[category] = ordered

        for t in self.transactions:
            if t.merchant_name and self._is_spending(t):
                merchant_spending[t.merchant_name] = (
                    merchant_spending.get(t.merchant_name, Decimal("0")) + t.amount
                )

        top_merchants = sorted(merchant_spending.items(), key=lambda x: x[1], reverse=True)[:5]
        for merchant, total_spent in top_merchants:
            if total_spent > 200:
                insights.append(
                    self._create_insight(
                        "merchant_loyalty",
                        title=f"Frequent Purchases at {merchant}",
                        description=f"You shop at {merchant} regularly — check for loyalty or membership perks.",
                        priority="low",
                        data={"merchant": merchant, "total_spent": float(total_spent)},
                        context="Evaluated over the last 90 days.",
                    )
                )
        electronics_spending = self._positive_sum(
            [
                t
                for t in self.transactions
                if self._normalize_category(t.category_primary) == "GENERAL_MERCHANDISE"
            ]
        )
        if electronics_spending > Decimal("800"):
            historical_avg = 0
            if category_history and "GENERAL_MERCHANDISE" in category_history:
                past_amounts = category_history["GENERAL_MERCHANDISE"][:-1]
                if past_amounts:
                    historical_avg = sum(past_amounts) / len(past_amounts)
            insights.append(
                self._create_insight(
                    "category_trend",
                    title="Electronics Spending Spike",
                    description=(
                        "Electronics purchases are far above normal — review recent big-ticket orders. "
                        f"Typical spend was about ${historical_avg:.0f} before this spike."
                    ),
                    priority="medium",
                    data={
                        "total_spent": float(electronics_spending),
                        "historical_average": float(historical_avg),
                    },
                    context="Current month compared to typical monthly spending.",
                )
            )

        # Merchant bundling opportunity
        bundling_window_start = datetime.utcnow() - timedelta(days=45)
        category_merchants: Dict[str, Dict[str, Dict[str, Any]]] = defaultdict(dict)
        for t in self.transactions:
            if not self._is_spending(t) or t.date < bundling_window_start:
                continue
            category = self._normalize_category(t.category_primary)
            merchant = self._normalize_merchant_label(t)
            if not category or not merchant:
                continue
            merchant_bucket = category_merchants[category].setdefault(
                merchant, {"count": 0, "amount": Decimal("0")}
            )
            merchant_bucket["count"] += 1
            merchant_bucket["amount"] += t.amount

        bundling_candidates: List[Dict[str, Any]] = []
        for category, merchants in category_merchants.items():
            frequent_merchants = [
                (merchant, meta) for merchant, meta in merchants.items() if meta["count"] >= 2
            ]
            if len(frequent_merchants) >= 3:
                total_visits = sum(meta["count"] for _, meta in frequent_merchants)
                total_spent = sum(meta["amount"] for _, meta in frequent_merchants)
                bundling_candidates.append(
                    {
                        "category": category,
                        "merchant_count": len(frequent_merchants),
                        "total_visits": total_visits,
                        "total_spent": total_spent,
                        "sample_merchants": [name for name, _ in frequent_merchants[:3]],
                    }
                )

        bundling_candidates.sort(key=lambda item: item["total_spent"], reverse=True)
        if bundling_candidates:
            candidate = bundling_candidates[0]
            category_label = self._format_category_label(candidate["category"])
            insights.append(
                self._create_insight(
                    "merchant_bundling",
                    title=f"Bundle {category_label} Visits",
                    description=f"You shop at {candidate['merchant_count']} different {category_label.lower()} merchants ({candidate['total_visits']} visits) — consolidating at one with a loyalty program could stretch rewards.",
                    priority="medium",
                    data={
                        "category": category_label,
                        "merchant_count": candidate["merchant_count"],
                        "total_visits": candidate["total_visits"],
                        "total_spent": float(candidate["total_spent"]),
                        "sample_merchants": candidate["sample_merchants"],
                    },
                    context="Based on roughly the last 45 days of activity.",
                )
            )

        # High-frequency small purchases
        small_window_start = datetime.utcnow() - timedelta(days=30)
        small_transactions = [
            t
            for t in self.transactions
            if self._is_spending(t)
            and t.date >= small_window_start
            and t.amount <= self.SMALL_PURCHASE_THRESHOLD
        ]
        if len(small_transactions) >= 12:
            total_small = sum(t.amount for t in small_transactions)
            unique_merchants = {
                self._normalize_merchant_label(t) for t in small_transactions if t.merchant_name or t.name
            }
            if total_small >= Decimal("50") and len(unique_merchants) >= 3:
                insights.append(
                    self._create_insight(
                        "high_frequency_small",
                        title="Frequent Small Purchases",
                        description=f"You made {len(small_transactions)} purchases under $10 (totaling ${float(total_small):.2f}) — batching essentials or buying in bulk could reduce fees.",
                        priority="low",
                        data={
                            "transaction_count": len(small_transactions),
                            "total_spent": float(total_small),
                            "unique_merchants": len(unique_merchants),
                        },
                        context="Look-back window: last 30 days.",
                    )
                )

        # Category subscription opportunity (fitness / memberships)
        membership_window_start = datetime.utcnow() - timedelta(days=60)
        membership_transactions: List[models.Transaction] = []
        for t in self.transactions:
            if not self._is_spending(t) or t.date < membership_window_start:
                continue
            category = self._normalize_category(t.category_primary)
            merchant_name = self._normalize_merchant_label(t)
            name_lower = merchant_name.lower()
            if category in self.FITNESS_CATEGORIES or self._matches_keywords(name_lower, self.FITNESS_KEYWORDS):
                membership_transactions.append(t)

        if len(membership_transactions) >= 3:
            membership_total = sum(t.amount for t in membership_transactions)
            membership_merchants = {
                self._normalize_merchant_label(t) for t in membership_transactions
            }
            if membership_total >= Decimal("150") and len(membership_merchants) >= 2:
                insights.append(
                    self._create_insight(
                        "category_subscription_opportunity",
                        title="Fitness Membership Opportunity",
                        description=f"You spent ${float(membership_total):.2f} on fitness visits across {len(membership_merchants)} spots — a membership plan could be cheaper.",
                        priority="medium",
                        data={
                            "merchant_count": len(membership_merchants),
                            "total_spent": float(membership_total),
                            "transaction_count": len(membership_transactions),
                        },
                        context="Evaluated over the last 60 days.",
                    )
                )

        # Payment method optimization for large travel spend
        travel_window_start = datetime.utcnow() - timedelta(days=90)
        travel_transactions = [
            t
            for t in self.transactions
            if self._is_spending(t)
            and t.date >= travel_window_start
            and t.amount >= Decimal("250")
            and (
                self._normalize_category(t.category_primary) in self.TRAVEL_CATEGORIES
                or self._matches_keywords(self._normalize_merchant_label(t).lower(), self.AIRLINE_KEYWORDS)
            )
        ]
        if len(travel_transactions) >= 2:
            travel_total = sum(t.amount for t in travel_transactions)
            if travel_total >= Decimal("500"):
                largest_purchase = max(travel_transactions, key=lambda t: t.amount)
                insights.append(
                    self._create_insight(
                        "payment_method_optimization",
                        title="Optimize Travel Rewards",
                        description=f"{len(travel_transactions)} large travel purchases totaling ${float(travel_total):.2f} might earn more rewards with a travel-tier card.",
                        priority="medium",
                        data={
                            "transaction_count": len(travel_transactions),
                            "total_spent": float(travel_total),
                            "largest_purchase": float(largest_purchase.amount),
                            "largest_merchant": self._normalize_merchant_label(largest_purchase),
                        },
                        context="Based on large travel transactions in the last 90 days.",
                    )
                )

        # Duplicate services (cloud storage, streaming, productivity)
        service_window_start = datetime.utcnow() - timedelta(days=45)
        service_usage: Dict[str, Dict[str, Decimal]] = defaultdict(dict)
        for t in self.transactions:
            if not self._is_spending(t) or t.date < service_window_start:
                continue
            merchant_name = self._normalize_merchant_label(t)
            name_lower = merchant_name.lower()
            for service_key, meta in self.DUPLICATE_SERVICE_KEYWORDS.items():
                if self._matches_keywords(name_lower, meta["keywords"]):
                    usage = service_usage[service_key].setdefault(merchant_name, Decimal("0"))
                    usage += t.amount
                    service_usage[service_key][merchant_name] = usage

        for service_key, merchants in service_usage.items():
            if len(merchants) < 2:
                continue
            total_spent = sum(merchants.values())
            label = self.DUPLICATE_SERVICE_KEYWORDS[service_key]["label"]
            merchant_names = list(merchants.keys())
            insights.append(
                self._create_insight(
                    "duplicate_services",
                    title=f"Duplicate {label.title()} Services",
                    description=f"You paid for multiple {label} providers ({', '.join(merchant_names[:3])}) — consolidating could reduce overlap.",
                    priority="low",
                    data={
                        "service_type": label,
                        "merchant_count": len(merchant_names),
                        "total_spent": float(total_spent),
                        "merchants": merchant_names,
                    },
                    context="Review overlapping services from the last 45 days.",
                )
            )
            break

        return insights

    def _generate_behavioral_insights(self) -> List[Dict[str, Any]]:
        insights: List[Dict[str, Any]] = []
        weekend_spending = sum(
            t.amount for t in self.transactions if t.date.weekday() >= 5 and self._is_spending(t)
        )
        weekday_spending = sum(
            t.amount for t in self.transactions if t.date.weekday() < 5 and self._is_spending(t)
        )
        if weekday_spending and weekend_spending > weekday_spending * Decimal("1.4"):
            insights.append(
                self._create_insight(
                    "weekend_pattern",
                    title="Weekend Spending Pattern",
                    description="Weekend spending is significantly higher than weekdays — a weekend budget may help.",
                    priority="medium",
                    data={
                        "weekend_spending": float(weekend_spending),
                        "weekday_spending": float(weekday_spending),
                    },
                    context="Weekend vs weekday spending over the last 90 days.",
                )
            )

        evening_txns = [
            t
            for t in self.transactions
            if t.payment_metadata and "evening" in t.payment_metadata.lower() and self._is_spending(t)
        ]
        if self.transactions and len(evening_txns) > len(self.transactions) * 0.3:
            insights.append(
                self._create_insight(
                    "time_of_day_pattern",
                    title="Evening Spending Trend",
                    description="A large share of purchases occur in the evening — consider setting reminders before late-night spending.",
                    priority="low",
                    data={
                        "evening_transactions": len(evening_txns),
                        "total_transactions": len(self.transactions),
                    },
                    context="Time-of-day pattern over the last 90 days.",
                )
            )
        return insights

    def _generate_transportation_insights(self) -> List[Dict[str, Any]]:
        insights: List[Dict[str, Any]] = []
        transportation_transactions = [
            t
            for t in self.transactions
            if self._normalize_category(t.category_primary) in {"TRANSPORTATION", "TRAVEL"}
            or any(keyword in (t.name or "").lower() for keyword in ["uber", "lyft", "taxi", "gas", "parking"])
        ]
        if not transportation_transactions:
            return insights

        total_transportation = self._positive_sum(transportation_transactions)
        rideshare_spending = sum(
            t.amount
            for t in transportation_transactions
            if any(keyword in (t.name or "").lower() for keyword in self.RIDESHARE_KEYWORDS)
            and self._is_spending(t)
        )
        if rideshare_spending > 150:
            insights.append(
                self._create_insight(
                    "transportation_mix",
                    title="High Rideshare Spending",
                    description="You spent heavily on rideshares — a transit pass or carpooling might reduce costs.",
                    priority="medium",
                    data={
                        "rideshare_spending": float(rideshare_spending),
                        "total_transportation": float(total_transportation),
                    },
                    context="Last 90 days of transportation transactions.",
                )
            )

        parking_transactions = [
            t for t in transportation_transactions if "parking" in (t.name or "").lower()
        ]
        if len(parking_transactions) >= 5:
            insights.append(
                self._create_insight(
                    "transportation_mix",
                    title="Parking Fees Adding Up",
                    description="Frequent parking fees suggest a monthly parking pass could save money.",
                    priority="low",
                    data={
                        "transactions": len(parking_transactions),
                        "total_spent": float(self._positive_sum(parking_transactions)),
                    },
                    context="Parking transactions during the last 90 days.",
                )
            )
        return insights

    def _generate_cross_user_affinity_insights(self) -> List[Dict[str, Any]]:
        insights: List[Dict[str, Any]] = []
        user_merchants: Dict[str, Dict[str, Optional[str]]] = {}
        for t in self.transactions:
            if not t.merchant_name or not self._is_spending(t):
                continue
            merchant = (t.merchant_name or "").strip()
            if not merchant:
                continue
            user_merchants[merchant] = {
                "category": self._normalize_category(t.category_primary),
                "bucket": self._category_bucket(t.category_primary, merchant),
            }
        if not user_merchants:
            return insights

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=90)

        rows = (
            self.db.query(
                models.Transaction.merchant_name,
                models.Transaction.category_primary,
                models.Transaction.user_id,
            )
            .filter(models.Transaction.merchant_name.isnot(None))
            .filter(models.Transaction.merchant_name != "")
            .filter(models.Transaction.date >= start_date)
            .distinct()
            .all()
        )

        merchant_users: Dict[str, set[int]] = defaultdict(set)
        merchant_categories: Dict[str, Optional[str]] = {}
        merchant_buckets: Dict[str, Optional[str]] = {}
        for merchant, category, user_id in rows:
            name = (merchant or "").strip()
            if not name:
                continue
            merchant_users[name].add(user_id)
            merchant_categories.setdefault(name, self._normalize_category(category))
            merchant_buckets.setdefault(name, self._category_bucket(category, name))

        # ensure current user present in sets
        for merchant, meta in user_merchants.items():
            merchant_users.setdefault(merchant, set()).add(self.user_id)
            merchant_categories.setdefault(merchant, meta.get("category"))
            merchant_buckets.setdefault(merchant, meta.get("bucket"))

        candidate_scores: Dict[str, Dict[str, Any]] = {}
        for base_merchant, meta in user_merchants.items():
            base_category = meta.get("category") or merchant_categories.get(base_merchant)
            base_bucket = meta.get("bucket") or merchant_buckets.get(base_merchant)
            if not base_bucket:
                continue
            base_users = merchant_users.get(base_merchant, set())
            if len(base_users) < 5:
                continue
            for candidate, candidate_users in merchant_users.items():
                if candidate in user_merchants or candidate == base_merchant:
                    continue
                candidate_category = merchant_categories.get(candidate)
                candidate_bucket = merchant_buckets.get(candidate)
                if not candidate_bucket or candidate_bucket != base_bucket:
                    continue
                overlap_users = base_users & candidate_users
                if len(overlap_users) < 5:
                    continue
                confidence = len(overlap_users) / len(base_users)
                adoption = len(candidate_users) / max(len(base_users), 1)
                score = confidence * adoption
                existing = candidate_scores.get(candidate)
                if not existing or score > existing["score"]:
                    candidate_scores[candidate] = {
                        "score": score,
                        "base": base_merchant,
                        "confidence": confidence,
                        "adoption": adoption,
                        "overlap_count": len(overlap_users),
                        "base_population": len(base_users),
                        "bucket": base_bucket,
                        "category": base_category,
                    }

        if not candidate_scores:
            return insights

        top_candidates = sorted(
            candidate_scores.items(), key=lambda item: item[1]["score"], reverse=True
        )[:3]

        for candidate, meta in top_candidates:
            confidence_pct = meta["confidence"] * 100
            bucket_label = self.CATEGORY_BUCKET_LABELS.get(meta.get("bucket") or "")
            category_label = merchant_categories.get(meta["base"]) or merchant_categories.get(candidate)
            category_text = bucket_label or (
                self._format_category_label(category_label) if category_label else "this category"
            )
            insights.append(
                self._create_insight(
                    "cross_user_affinity",
                    title=f"Users who love {meta['base']} also enjoy {candidate}",
                    description=(
                        f"Within {category_text}, fans of {meta['base']} frequently visit {candidate}. "
                        "Consider giving it a try."
                    ),
                    priority="medium",
                    data={
                        "base_merchant": meta["base"],
                        "recommended_merchant": candidate,
                        "confidence_percentage": round(confidence_pct, 1),
                        "supporting_users": meta["overlap_count"],
                    },
                    context="Aggregated across similar users in the last 90 days.",
                )
            )
        return insights

    def _generate_sustainability_insights(self) -> List[Dict[str, Any]]:
        insights: List[Dict[str, Any]] = []
        if not self.transactions:
            return insights

        total_spending = sum(t.amount for t in self.transactions if self._is_spending(t))
        local_transactions = [t for t in self.transactions if self._is_local_transaction(t)]
        local_spending = sum(t.amount for t in local_transactions)
        local_percentage = (local_spending / total_spending * 100) if total_spending > 0 else 0

        if local_spending > 0:
            insights.append(
                self._create_insight(
                    "local_support",
                    title="Local Business Support",
                    description=f"{local_percentage:.0f}% of spending went to local businesses — great job supporting your community!",
                    priority="low",
                    data={
                        "local_spending": float(local_spending),
                        "total_spending": float(total_spending),
                        "local_percentage": round(float(local_percentage), 1),
                    },
                    context="Local vs total spending over the last 90 days.",
                )
            )

        # Local shop loyalty (repeat visits)
        local_visit_counts: Dict[str, int] = defaultdict(int)
        for t in local_transactions:
            merchant = self._normalize_merchant_label(t)
            if merchant:
                local_visit_counts[merchant] += 1
        repeat_merchants = [m for m, count in local_visit_counts.items() if count >= 3]
        repeat_visits = sum(local_visit_counts[m] for m in repeat_merchants)
        if len(repeat_merchants) >= 2:
            insights.append(
                self._create_insight(
                    "local_shop_loyalty",
                    title="Local Shop Loyalty",
                    description=f"You visited {len(repeat_merchants)} local spots 3+ times ({repeat_visits} visits total) — strong hometown support.",
                    priority="low",
                    data={
                        "merchant_count": len(repeat_merchants),
                        "repeat_visits": repeat_visits,
                        "merchants": repeat_merchants[:5],
                    },
                    context="Repeat visits counted over the last 90 days.",
                )
            )

        # Low-waste purchase trend
        low_waste_window = datetime.utcnow() - timedelta(days=90)
        low_waste_txns = [
            t
            for t in self.transactions
            if self._is_spending(t)
            and t.date >= low_waste_window
            and (
                self._normalize_category(t.category_primary) in self.LOW_WASTE_CATEGORIES
                or self._matches_keywords(self._normalize_merchant_label(t).lower(), self.LOW_WASTE_KEYWORDS)
            )
        ]
        if len(low_waste_txns) >= 3:
            low_waste_total = sum(t.amount for t in low_waste_txns)
            insights.append(
                self._create_insight(
                    "low_waste_trend",
                    title="Low-Waste Purchase Trend",
                    description=f"You made {len(low_waste_txns)} thrift or secondhand purchases — supporting circular consumption.",
                    priority="medium",
                    data={
                        "transaction_count": len(low_waste_txns),
                        "total_spent": float(low_waste_total),
                    },
                    context="Based on purchases tagged as thrift/secondhand in the last 90 days.",
                )
            )

        # Air travel footprint indicator
        air_window_start = datetime.utcnow() - timedelta(days=90)
        airline_transactions = [
            t
            for t in self.transactions
            if self._is_spending(t)
            and t.date >= air_window_start
            and (
                self._normalize_category(t.category_primary) in {"AIRLINES", "AIR_TRAVEL", "TRAVEL"}
                or self._matches_keywords(self._normalize_merchant_label(t).lower(), self.AIRLINE_KEYWORDS)
            )
        ]
        if len(airline_transactions) >= 2:
            airline_total = sum(t.amount for t in airline_transactions)
            insights.append(
                self._create_insight(
                    "air_travel_footprint",
                    title="Air Travel Footprint",
                    description=f"You had {len(airline_transactions)} airline purchases this quarter — air travel is a major carbon driver.",
                    priority="medium",
                    data={
                        "transaction_count": len(airline_transactions),
                        "total_spent": float(airline_total),
                    },
                    context="Airline-tagged spend over the last 90 days.",
                )
            )

        # Seasonal local support trend (current month vs previous)
        current_month_start = self._month_start(datetime.utcnow())
        previous_month_start = self._month_start(current_month_start - timedelta(days=1))
        current_local = sum(t.amount for t in local_transactions if t.date >= current_month_start)
        previous_local = sum(
            t.amount for t in local_transactions if previous_month_start <= t.date < current_month_start
        )
        current_total_month = sum(
            t.amount for t in self.transactions if self._is_spending(t) and t.date >= current_month_start
        )
        previous_total_month = sum(
            t.amount
            for t in self.transactions
            if self._is_spending(t) and previous_month_start <= t.date < current_month_start
        )
        if current_total_month > 0 and previous_total_month > 0:
            current_share = current_local / current_total_month
            previous_share = previous_local / previous_total_month
            if current_share - previous_share >= Decimal("0.05"):
                insights.append(
                    self._create_insight(
                        "seasonal_local_support",
                        title="Local Support Trend",
                        description=f"Local-business spending rose from {previous_share * 100:.0f}% to {current_share * 100:.0f}% this month — strong seasonal boost.",
                        priority="low",
                        data={
                            "current_share": round(float(current_share * 100), 1),
                            "previous_share": round(float(previous_share * 100), 1),
                        },
                        context="Comparing current vs previous month.",
                    )
                )

        return insights

    def _generate_consumption_insights(self) -> List[Dict[str, Any]]:
        insights: List[Dict[str, Any]] = []
        current_month_start = datetime.utcnow().replace(day=1)
        last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)

        current_month_spending: Dict[str, Decimal] = defaultdict(Decimal)
        last_month_spending: Dict[str, Decimal] = defaultdict(Decimal)

        for t in self.transactions:
            category = self._normalize_category(t.category_primary)
            if not category or not self._is_spending(t):
                continue
            if t.date >= current_month_start:
                current_month_spending[category] += t.amount
            elif t.date >= last_month_start:
                last_month_spending[category] += t.amount

        for category, current_amount in current_month_spending.items():
            previous_amount = last_month_spending.get(category, Decimal("0"))
            if previous_amount == 0:
                continue
            change_pct = ((current_amount - previous_amount) / previous_amount) * 100
            if abs(change_pct) >= 25:
                direction = "Increased" if change_pct > 0 else "Decreased"
                if change_pct > 0:
                    priority = "high" if change_pct >= 40 else "medium"
                else:
                    priority = "high" if abs(change_pct) >= 85 else "low"
                insights.append(
                    self._create_insight(
                        "category_trend",
                        title=f"{self._format_category_label(category)} Spending {direction}",
                        description=f"{self._format_category_label(category)} spending has {direction.lower()} by {abs(change_pct):.0f}%.",
                        priority=priority,
                        data={
                            "category": self._format_category_label(category),
                            "change_percentage": float(change_pct),
                            "current_amount": float(current_amount),
                            "previous_amount": float(previous_amount),
                        },
                        context="Current month compared to previous month.",
                    )
                )

        return insights

    def _generate_income_insights(self) -> List[Dict[str, Any]]:
        insights: List[Dict[str, Any]] = []
        income_transactions = [
            t for t in self.transactions if t.amount is not None and t.amount < 0
        ]
        if not income_transactions:
            insights.append(
                self._create_insight(
                    "income_pattern",
                    title="No Income Activity",
                    description="No recent income activity — enable notifications or verify payroll.",
                    priority="medium",
                    data={},
                    context="No deposits detected over the past 30 days.",
                )
            )
            return insights

        income_by_merchant: Dict[str, List[models.Transaction]] = defaultdict(list)
        for t in income_transactions:
            if t.merchant_name:
                income_by_merchant[t.merchant_name].append(t)

        for merchant, txns in income_by_merchant.items():
            if len(txns) >= 3:
                avg_amount = sum(t.amount for t in txns) / len(txns)
                insights.append(
                    self._create_insight(
                        "income_pattern",
                        title=f"Recurring Deposits from {merchant}",
                        description=f"{merchant} deposits arrive consistently — automate savings on payday.",
                        priority="medium",
                        data={
                            "transactions": len(txns),
                            "average_deposit": float(avg_amount),
                        },
                        context="Recurring deposit pattern over the last 90 days.",
                    )
                )
        return insights

    def _generate_goal_insights(self) -> List[Dict[str, Any]]:
        insights: List[Dict[str, Any]] = []
        total_balance = sum(
            (acc.current_balance or 0)
            for acc in self.accounts
            if (acc.subtype or "").lower() not in {"checking", "paypal", "venmo"}
        )
        if total_balance > 500:
            insights.append(
                self._create_insight(
                    "savings_milestone",
                    title="Savings Milestone",
                    description=f"Current liquid savings total ${total_balance:.0f}. Set a specific target to keep momentum.",
                    priority="low",
                    data={"current_savings": float(total_balance)},
                    context="Snapshot of current liquid balances.",
                )
            )
        return insights
