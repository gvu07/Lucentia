import json
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
from . import models, schemas
from .insight_registry import get_domain_meta, get_family_meta

def _as_decimal(value):
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))

# User CRUD operations
def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    from .auth import get_password_hash
    
    db_user = models.User(
        email=user.email,
        hashed_password=get_password_hash(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()

def get_user(db: Session, user_id: int) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()

def upsert_plaid_item(
    db: Session,
    user_id: int,
    item_id: str,
    access_token: str,
    institution_name: Optional[str] = None,
    webhook_status: Optional[str] = None,
) -> models.PlaidItem:
    plaid_item = (
        db.query(models.PlaidItem)
        .filter(models.PlaidItem.item_id == item_id)
        .first()
    )
    if plaid_item:
        plaid_item.access_token = access_token
        plaid_item.institution_name = institution_name or plaid_item.institution_name
        plaid_item.webhook_status = webhook_status or plaid_item.webhook_status
        plaid_item.updated_at = datetime.utcnow()
    else:
        plaid_item = models.PlaidItem(
            user_id=user_id,
            item_id=item_id,
            access_token=access_token,
            institution_name=institution_name,
            webhook_status=webhook_status,
        )
        db.add(plaid_item)
    db.commit()
    db.refresh(plaid_item)
    return plaid_item

def get_plaid_items_by_user(db: Session, user_id: int) -> List[models.PlaidItem]:
    return (
        db.query(models.PlaidItem)
        .filter(models.PlaidItem.user_id == user_id)
        .order_by(models.PlaidItem.created_at.asc())
        .all()
    )

def get_plaid_item_by_id(db: Session, plaid_item_id: int) -> Optional[models.PlaidItem]:
    return (
        db.query(models.PlaidItem)
        .filter(models.PlaidItem.id == plaid_item_id)
        .first()
    )

def update_plaid_item_last_synced(db: Session, plaid_item_id: int, synced_at: Optional[datetime] = None) -> None:
    synced_time = synced_at or datetime.utcnow()
    (
        db.query(models.PlaidItem)
        .filter(models.PlaidItem.id == plaid_item_id)
        .update({"last_synced_at": synced_time}, synchronize_session=False)
    )
    db.commit()

def get_latest_transaction_date_for_item(db: Session, plaid_item_id: int) -> Optional[datetime]:
    last_date = (
        db.query(func.max(models.Transaction.date))
        .join(models.Account, models.Account.id == models.Transaction.account_id)
        .filter(models.Account.plaid_item_id == plaid_item_id)
        .scalar()
    )
    return last_date

def record_plaid_sync_event(
    db: Session,
    user_id: int,
    plaid_item_id: int,
    *,
    transactions_count: int,
    pages_fetched: int,
    event_type: str = "exchange",
) -> models.PlaidSyncEvent:
    event = models.PlaidSyncEvent(
        user_id=user_id,
        plaid_item_id=plaid_item_id,
        event_type=event_type,
        transactions_count=transactions_count,
        pages_fetched=pages_fetched,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

# Account CRUD operations
def create_account(db: Session, account: schemas.AccountCreate) -> models.Account:
    db_account = models.Account(**account.dict())
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account

def get_accounts_by_user(db: Session, user_id: int) -> List[models.Account]:
    return db.query(models.Account).filter(
        models.Account.user_id == user_id,
        models.Account.is_active == True
    ).all()

def upsert_account_from_plaid(
    db: Session,
    user_id: int,
    plaid_item_id: int,
    account_payload: Dict[str, Any],
) -> models.Account:
    plaid_account_id = account_payload["account_id"]
    balances = account_payload.get("balances", {}) or {}
    currency_code = (
        balances.get("iso_currency_code")
        or balances.get("unofficial_currency_code")
        or "USD"
    )
    db_account = (
        db.query(models.Account)
        .filter(models.Account.plaid_account_id == plaid_account_id)
        .first()
    )
    payload = {
        "user_id": user_id,
        "plaid_item_id": plaid_item_id,
        "plaid_account_id": plaid_account_id,
        "name": account_payload.get("name") or "Linked Account",
        "official_name": account_payload.get("official_name"),
        "type": account_payload.get("type") or "unknown",
        "subtype": account_payload.get("subtype"),
        "available_balance": _as_decimal(balances.get("available")),
        "current_balance": _as_decimal(balances.get("current")),
        "currency_code": currency_code,
    }
    if db_account:
        for key, value in payload.items():
            if value is not None:
                setattr(db_account, key, value)
        db_account.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_account)
        return db_account

    db_account = models.Account(**payload)
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account

def update_account_balances(db: Session, account_id: int, available_balance: Decimal, current_balance: Decimal):
    db_account = db.query(models.Account).filter(models.Account.id == account_id).first()
    if db_account:
        db_account.available_balance = available_balance
        db_account.current_balance = current_balance
        db_account.updated_at = datetime.utcnow()
        db.commit()

# Transaction CRUD operations
def create_transaction(db: Session, transaction: schemas.TransactionCreate) -> models.Transaction:
    db_transaction = models.Transaction(**transaction.dict())
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

def upsert_transaction_from_plaid(
    db: Session,
    user_id: int,
    account_id: int,
    transaction_payload: Dict[str, Any],
) -> models.Transaction:
    plaid_transaction_id = transaction_payload["transaction_id"]
    db_transaction = get_transaction_by_plaid_id(db, plaid_transaction_id)

    txn_date = transaction_payload.get("date") or transaction_payload.get("authorized_date")
    if isinstance(txn_date, str):
        txn_date = datetime.strptime(txn_date, "%Y-%m-%d")
    elif isinstance(txn_date, datetime):
        pass
    else:
        txn_date = datetime.utcnow()

    categories = transaction_payload.get("category") or []
    pf_category = transaction_payload.get("personal_finance_category") or {}
    category_primary = categories[0] if categories else pf_category.get("primary")
    category_detailed = categories[1] if len(categories) > 1 else pf_category.get("detailed")
    location = transaction_payload.get("location") or {}
    payment_meta = transaction_payload.get("payment_meta") or {}
    metadata_payload = payment_meta or None
    currency_code = (
        transaction_payload.get("iso_currency_code")
        or transaction_payload.get("unofficial_currency_code")
        or "USD"
    )

    payload = {
        "user_id": user_id,
        "account_id": account_id,
        "plaid_transaction_id": plaid_transaction_id,
        "amount": _as_decimal(transaction_payload.get("amount")),
        "currency_code": currency_code,
        "date": txn_date,
        "name": transaction_payload.get("name") or transaction_payload.get("merchant_name") or "Transaction",
        "merchant_name": transaction_payload.get("merchant_name"),
        "category_primary": category_primary,
        "category_detailed": category_detailed,
        "category_confidence_level": pf_category.get("confidence_level"),
        "payment_channel": transaction_payload.get("payment_channel"),
        "payment_metadata": json.dumps(metadata_payload) if metadata_payload else None,
        "location_city": location.get("city"),
        "location_region": location.get("region"),
        "location_country": location.get("country"),
        "is_pending": transaction_payload.get("pending", False),
        "is_recurring": transaction_payload.get("recurring", False),
    }

    if db_transaction:
        for key, value in payload.items():
            setattr(db_transaction, key, value)
        db_transaction.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_transaction)
        return db_transaction

    db_transaction = models.Transaction(**payload)
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

def get_transactions_by_user(
    db: Session, 
    user_id: int, 
    limit: int = 100, 
    offset: int = 0,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> List[models.Transaction]:
    query = db.query(models.Transaction).filter(models.Transaction.user_id == user_id)
    
    if start_date:
        query = query.filter(models.Transaction.date >= start_date)
    if end_date:
        query = query.filter(models.Transaction.date <= end_date)
    
    return query.order_by(models.Transaction.date.desc()).limit(limit).offset(offset).all()

def count_transactions_by_user(
    db: Session,
    user_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> int:
    query = db.query(func.count(models.Transaction.id)).filter(models.Transaction.user_id == user_id)
    
    if start_date:
        query = query.filter(models.Transaction.date >= start_date)
    if end_date:
        query = query.filter(models.Transaction.date <= end_date)
    
    return query.scalar() or 0

def get_transaction_by_plaid_id(db: Session, plaid_transaction_id: str) -> Optional[models.Transaction]:
    return db.query(models.Transaction).filter(
        models.Transaction.plaid_transaction_id == plaid_transaction_id
    ).first()

def get_spending_by_category(
    db: Session, 
    user_id: int, 
    start_date: datetime, 
    end_date: datetime
) -> Dict[str, Decimal]:
    results = db.query(
        models.Transaction.category_primary,
        func.sum(models.Transaction.amount).label('total_spent')
    ).filter(
        models.Transaction.user_id == user_id,
        models.Transaction.date >= start_date,
        models.Transaction.date <= end_date,
        models.Transaction.category_primary.isnot(None),
        models.Transaction.amount > 0
    ).group_by(models.Transaction.category_primary).all()
    
    return {category: Decimal(str(total)) for category, total in results}

def get_monthly_spending_trend(
    db: Session, 
    user_id: int, 
    months: int = 6
) -> Dict[str, Decimal]:
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30*months)
    
    results = db.query(
        extract('year', models.Transaction.date).label('year'),
        extract('month', models.Transaction.date).label('month'),
        func.sum(models.Transaction.amount).label('total_spent')
    ).filter(
        models.Transaction.user_id == user_id,
        models.Transaction.date >= start_date,
        models.Transaction.date <= end_date
    ).group_by(
        extract('year', models.Transaction.date),
        extract('month', models.Transaction.date)
    ).order_by('year', 'month').all()
    
    return {f"{int(year)}-{int(month):02d}": Decimal(str(total)) for year, month, total in results}

# Insight CRUD operations
def create_insight(db: Session, insight: schemas.InsightCreate) -> models.Insight:
    db_insight = models.Insight(
        user_id=insight.user_id,
        category=insight.domain,
        type=insight.family,
        title=insight.title,
        description=insight.description,
        data=insight.data,
        priority=insight.priority,
        expires_at=insight.expires_at,
    )
    db.add(db_insight)
    db.commit()
    db.refresh(db_insight)
    return db_insight

def get_insights_by_user_and_category(
    db: Session, 
    user_id: int, 
    category: str,
    limit: int = 10
) -> List[models.Insight]:
    return db.query(models.Insight).filter(
        models.Insight.user_id == user_id,
        models.Insight.category == category,
        models.Insight.is_active == True
    ).order_by(models.Insight.created_at.desc()).limit(limit).all()

def get_all_insights_by_user(
    db: Session,
    user_id: int,
    limit: int = 50
) -> schemas.InsightsResponse:
    db_insights = db.query(models.Insight).filter(
        models.Insight.user_id == user_id,
        models.Insight.is_active == True
    ).order_by(models.Insight.created_at.desc()).limit(limit).all()

    domain_map: Dict[str, Dict[str, List[models.Insight]]] = {}
    for record in db_insights:
        domain_key = record.category or "spending_patterns"
        family_key = record.type or "uncategorized"
        domain_bucket = domain_map.setdefault(domain_key, {})
        domain_bucket.setdefault(family_key, []).append(record)

    domain_groups: List[schemas.InsightDomainGroup] = []
    ordered_domains = sorted(
        domain_map.keys(),
        key=lambda key: get_domain_meta(key).get("order", 999)
    )

    for domain_key in ordered_domains:
        domain_meta = get_domain_meta(domain_key)
        families_data: List[schemas.InsightFamilyGroup] = []
        for family_key, records in domain_map[domain_key].items():
            family_meta = get_family_meta(family_key)
            response_items = [
                schemas.InsightResponse(
                    id=insight.id,
                    user_id=insight.user_id,
                    domain=domain_key,
                    family=family_key,
                    title=insight.title,
                    description=insight.description,
                    data=insight.data,
                    priority=insight.priority,
                    expires_at=insight.expires_at,
                    is_active=insight.is_active,
                    created_at=insight.created_at,
                )
                for insight in records
            ]
            families_data.append(
                schemas.InsightFamilyGroup(
                    key=family_key,
                    name=family_meta["name"],
                    description=family_meta.get("description"),
                    insights=response_items
                )
            )

        domain_groups.append(
            schemas.InsightDomainGroup(
                key=domain_key,
                name=domain_meta["name"],
                description=domain_meta.get("description"),
                families=families_data
            )
        )

    return schemas.InsightsResponse(domains=domain_groups)

def deactivate_insight(db: Session, insight_id: int):
    db_insight = db.query(models.Insight).filter(models.Insight.id == insight_id).first()
    if db_insight:
        db_insight.is_active = False
        db.commit()

def delete_insights_by_user(db: Session, user_id: int):
    db.query(models.Insight).filter(models.Insight.user_id == user_id).delete()
    db.commit()

# Dashboard data
def get_dashboard_summary(db: Session, user_id: int) -> Dict[str, Any]:
    currency_code = get_primary_currency_for_user(db, user_id)

    # Total balance
    total_balance = db.query(
        func.sum(models.Account.current_balance)
    ).filter(
        models.Account.user_id == user_id,
        models.Account.is_active == True
    ).scalar() or Decimal('0')
    
    # Monthly spending
    current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_spending = db.query(
        func.sum(models.Transaction.amount)
    ).filter(
        models.Transaction.user_id == user_id,
        models.Transaction.date >= current_month_start,
        models.Transaction.amount > 0,
        models.Transaction.currency_code == currency_code
    ).scalar() or Decimal('0')
    
    # Transaction count this month
    transaction_count = db.query(models.Transaction).filter(
        models.Transaction.user_id == user_id,
        models.Transaction.date >= current_month_start
    ).count()
    
    # Top categories this month
    top_categories = db.query(
        models.Transaction.category_primary,
        func.sum(models.Transaction.amount).label('total')
    ).filter(
        models.Transaction.user_id == user_id,
        models.Transaction.date >= current_month_start,
        models.Transaction.category_primary.isnot(None),
        models.Transaction.amount > 0,
        models.Transaction.currency_code == currency_code
    ).group_by(models.Transaction.category_primary).order_by(func.sum(models.Transaction.amount).desc()).limit(5).all()
    
    top_categories_dict = {category: Decimal(str(total)) for category, total in top_categories}
    
    return {
        "total_balance": Decimal(str(total_balance)),
        "monthly_spending": Decimal(str(monthly_spending)),
        "transaction_count": transaction_count,
        "top_categories": top_categories_dict,
        "currency_code": currency_code,
    }

def get_primary_currency_for_user(db: Session, user_id: int) -> str:
    account_currency = (
        db.query(
            models.Account.currency_code,
            func.count(models.Account.id).label("cnt")
        )
        .filter(models.Account.user_id == user_id)
        .group_by(models.Account.currency_code)
        .order_by(func.count(models.Account.id).desc())
        .first()
    )
    if account_currency and account_currency.currency_code:
        return account_currency.currency_code
    transaction_currency = (
        db.query(
            models.Transaction.currency_code,
            func.count(models.Transaction.id).label("cnt")
        )
        .filter(models.Transaction.user_id == user_id)
        .group_by(models.Transaction.currency_code)
        .order_by(func.count(models.Transaction.id).desc())
        .first()
    )
    if transaction_currency and transaction_currency.currency_code:
        return transaction_currency.currency_code
    return "USD"
