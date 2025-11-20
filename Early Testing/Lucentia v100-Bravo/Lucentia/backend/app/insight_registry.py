INSIGHT_DOMAINS = {
    "spending_patterns": {
        "name": "Spending Patterns",
        "description": "Recurring behaviors and merchant habits.",
        "order": 1,
    },
    "spending_trends": {
        "name": "Spending Trends",
        "description": "Month-over-month or category shifts.",
        "order": 2,
    },
    "financial_health": {
        "name": "Financial Health",
        "description": "Balances, fees, and cash buffers.",
        "order": 3,
    },
    "optimization_rewards": {
        "name": "Optimization & Rewards",
        "description": "Opportunities to save or earn more.",
        "order": 4,
    },
    "behavior_lifestyle": {
        "name": "Behavior & Lifestyle",
        "description": "Time-based or habit insights.",
        "order": 5,
    },
    "sustainability_local": {
        "name": "Sustainability & Local Impact",
        "description": "Local businesses and ethical spending.",
        "order": 6,
    },
    "income_cashflow": {
        "name": "Income & Cashflow",
        "description": "Deposits, paycheck patterns, and gaps.",
        "order": 7,
    },
    "long_term_goals": {
        "name": "Long-Term Goals",
        "description": "Savings milestones and planning.",
        "order": 8,
    },
}

INSIGHT_FAMILIES = {
    "burst_spending": {
        "domain": "spending_patterns",
        "name": "Burst Spending",
        "description": "Short windows of unusually dense activity.",
    },
    "category_spike": {
        "domain": "spending_trends",
        "name": "Category Spike",
        "description": "Significant increase in category spending.",
    },
    "delivery_vs_grocery": {
        "domain": "spending_patterns",
        "name": "Delivery vs Groceries",
        "description": "Delivery costs compared to grocery spending.",
    },
    "habit_frequency": {
        "domain": "behavior_lifestyle",
        "name": "Habit Frequency",
        "description": "Repeated discretionary habits.",
    },
    "merchant_switching": {
        "domain": "spending_patterns",
        "name": "Merchant Switching",
        "description": "Shifts between similar merchants.",
    },
    "favorite_merchants": {
        "domain": "spending_patterns",
        "name": "Favorite Merchants",
        "description": "High-frequency merchants.",
    },
    "lapsed_favorites": {
        "domain": "behavior_lifestyle",
        "name": "Lapsed Favorites",
        "description": "Merchants you haven’t visited recently.",
    },
    "subscription_volume": {
        "domain": "optimization_rewards",
        "name": "Subscription Volume",
        "description": "Recurring subscriptions overview.",
    },
    "cost_drift": {
        "domain": "spending_patterns",
        "name": "Cost Drift",
        "description": "Average spend that slowly increases.",
    },
    "subscription_price_change": {
        "domain": "spending_trends",
        "name": "Subscription Price Change",
        "description": "Subscription cost adjustments.",
    },
    "duplicate_subscription": {
        "domain": "optimization_rewards",
        "name": "Duplicate Subscription",
        "description": "Potential overlapping subscriptions.",
    },
    "category_saturation": {
        "domain": "spending_patterns",
        "name": "Category Saturation",
        "description": "Single category dominates total spending.",
    },
    "category_volatility": {
        "domain": "spending_patterns",
        "name": "Category Volatility",
        "description": "Large month-to-month category swings.",
    },
    "consistency_score": {
        "domain": "spending_patterns",
        "name": "Consistency Score",
        "description": "Predictability of monthly spending.",
    },
    "cash_buffer": {
        "domain": "financial_health",
        "name": "Cash Buffer",
        "description": "Checking vs savings opportunity.",
    },
    "balance_warning": {
        "domain": "financial_health",
        "name": "Balance Warning",
        "description": "Low account balances.",
    },
    "fee_detection": {
        "domain": "financial_health",
        "name": "Fee Detection",
        "description": "ATM or maintenance fees.",
    },
    "merchant_loyalty": {
        "domain": "optimization_rewards",
        "name": "Merchant Loyalty Opportunity",
        "description": "Frequent merchants with loyalty options.",
    },
    "merchant_bundling": {
        "domain": "optimization_rewards",
        "name": "Merchant Bundling",
        "description": "Similar merchants that could be consolidated.",
    },
    "high_frequency_small": {
        "domain": "optimization_rewards",
        "name": "High-Frequency Small Purchases",
        "description": "Frequent micro-purchases that could be batched.",
    },
    "category_subscription_opportunity": {
        "domain": "optimization_rewards",
        "name": "Category Subscription Opportunity",
        "description": "Category spend that resembles a membership.",
    },
    "payment_method_optimization": {
        "domain": "optimization_rewards",
        "name": "Payment Method Optimization",
        "description": "Large transactions better suited for bonus rewards.",
    },
    "duplicate_services": {
        "domain": "optimization_rewards",
        "name": "Duplicate Services",
        "description": "Multiple services offering the same benefit.",
    },
    "category_trend": {
        "domain": "spending_trends",
        "name": "Category Trend Shift",
        "description": "Category spending increase or decrease.",
    },
    "weekend_pattern": {
        "domain": "behavior_lifestyle",
        "name": "Weekend Pattern",
        "description": "Weekend vs weekday spending.",
    },
    "time_of_day_pattern": {
        "domain": "behavior_lifestyle",
        "name": "Time of Day Pattern",
        "description": "Spending concentrated in specific hours.",
    },
    "cross_user_affinity": {
        "domain": "behavior_lifestyle",
        "name": "Cross-User Affinity Recommendations",
        "description": "People with similar habits also enjoy these merchants or categories.",
    },
    "transportation_mix": {
        "domain": "behavior_lifestyle",
        "name": "Transportation Mix",
        "description": "Rideshare and parking behaviors.",
    },
    "local_support": {
        "domain": "sustainability_local",
        "name": "Local Support",
        "description": "Spending at local businesses.",
    },
    "local_shop_loyalty": {
        "domain": "sustainability_local",
        "name": "Local Shop Loyalty",
        "description": "Repeat visits to local merchants.",
    },
    "low_waste_trend": {
        "domain": "sustainability_local",
        "name": "Low-Waste Trend",
        "description": "Secondhand or thrift purchases.",
    },
    "air_travel_footprint": {
        "domain": "sustainability_local",
        "name": "Air Travel Footprint",
        "description": "Airline spending as a carbon signal.",
    },
    "seasonal_local_support": {
        "domain": "sustainability_local",
        "name": "Seasonal Local Support",
        "description": "Local share shift month-to-month.",
    },
    "income_pattern": {
        "domain": "income_cashflow",
        "name": "Income Pattern",
        "description": "Recurring deposits and cashflow gaps.",
    },
    "savings_milestone": {
        "domain": "long_term_goals",
        "name": "Savings Milestone",
        "description": "Progress toward savings goals.",
    },
    "restaurant_comeback": {
        "domain": "behavior_lifestyle",
        "name": "Restaurant Comeback",
        "description": "Suggests revisiting spots you haven’t been to in a while.",
        "default_priority": "medium",
    },
    "favorite_restaurant_push": {
        "domain": "behavior_lifestyle",
        "name": "Favorite Restaurant Suggestion",
        "description": "Highlights a favorite dining spot and reminds you to enjoy it again.",
        "default_priority": "medium",
    },
}


def get_domain_meta(domain_key: str) -> dict:
    return INSIGHT_DOMAINS.get(domain_key, {"name": domain_key.title(), "description": "", "order": 999})


def get_family_meta(family_key: str) -> dict:
    meta = INSIGHT_FAMILIES.get(family_key)
    if not meta:
        return {"domain": "spending_patterns", "name": family_key.replace("_", " ").title(), "description": ""}
    return meta
