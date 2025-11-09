from datetime import date, timedelta
from sqlmodel import Session, select
from .models import Transaction


def dining_trend(session: Session):
    txs = session.exec(select(Transaction)).all()
    if not txs:
        return {"curr_week": 0.0, "avg_week": 0.0, "pct_change": None}

    # Broader dining keyword detection
    dining_keywords = ["mcdonald", "starbucks", "restaurant", "burger", "coffee", "food", "eat"]
    dining_txs = [
        t for t in txs
        if (t.category and "food" in t.category.lower())
        or any(k in (t.name or "").lower() for k in dining_keywords)
    ]

    if not dining_txs:
        return {"curr_week": 0.0, "avg_week": 0.0, "pct_change": None}

    today = date.today()
    recent_start = today - timedelta(days=7)
    old_start = today - timedelta(days=8*7)

    # Current week spend
    curr_week = sum(t.amount for t in dining_txs if t.date >= recent_start)

    # Past 8 weeks (excluding this week)
    past_weeks = []
    d = old_start
    while d < recent_start:
        week_end = d + timedelta(days=7)
        week_spend = sum(t.amount for t in dining_txs if d <= t.date < week_end)
        past_weeks.append(week_spend)
        d = week_end

    avg_week = (sum(past_weeks) / len(past_weeks)) if past_weeks else 0.0
    pct_change = ((curr_week - avg_week) / avg_week * 100.0) if avg_week > 0 else None

    return {"curr_week": curr_week, "avg_week": avg_week, "pct_change": pct_change}
