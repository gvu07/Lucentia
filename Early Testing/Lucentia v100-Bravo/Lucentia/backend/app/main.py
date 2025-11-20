from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import datetime, timedelta, date, timezone
import time
import json
import logging
from .database import engine, get_db
from .models import Base
from .schemas import (
    UserCreate, UserLogin, UserResponse,
    PlaidLinkTokenResponse,
    PlaidExchangeTokenRequest, PlaidExchangeTokenResponse,
    DashboardData, InsightsResponse
)
from plaid.exceptions import ApiException
from . import crud, auth, plaid_client, insights
from .settings import settings
from .demo_seed import seed_demo_dataset, clear_demo_data

logger = logging.getLogger(__name__)

def _enum_to_str(value):
    return value.value if hasattr(value, "value") else value

def _normalize_datetime_param(value: Optional[datetime], *, is_end: bool = False) -> Optional[datetime]:
    if not value:
        return None
    if value.tzinfo:
        value = value.astimezone(timezone.utc)
    normalized = value.replace(tzinfo=None)
    if (
        is_end
        and normalized.hour == 0
        and normalized.minute == 0
        and normalized.second == 0
        and normalized.microsecond == 0
    ):
        normalized = normalized + timedelta(days=1) - timedelta(microseconds=1)
    return normalized

def _fetch_with_retry(func, *args, retries=5, delay=2, **kwargs):
    for attempt in range(retries):
        try:
            return func(*args, **kwargs)
        except ApiException as e:
            try:
                error_data = json.loads(e.body) if e.body else {}
            except (TypeError, json.JSONDecodeError):
                error_data = {}
            if error_data.get("error_code") == "PRODUCT_NOT_READY":
                if attempt == retries - 1:
                    raise HTTPException(
                        status_code=503,
                        detail="Plaid is still preparing your account data. Please try again in a minute."
                    )
                time.sleep(delay * (attempt + 1))
                continue
            raise HTTPException(status_code=400, detail=error_data.get("error_message", str(e)))

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Lucentia API", version="1.0.0")

# Configure CORS
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to Lucentia API"}

# Authentication endpoints
@app.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=400, detail="Email already registered"
        )
    return crud.create_user(db=db, user=user)

@app.post("/login")
def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email=user_credentials.email)
    if not user or not auth.verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer", "user_id": user.id}

# Plaid integration endpoints
@app.post("/plaid/create_link_token", response_model=PlaidLinkTokenResponse)
def create_link_token(
    current_user: UserResponse = Depends(auth.get_current_user)
):
    try:
        token_data = plaid_client.create_link_token(str(current_user.id))
        return PlaidLinkTokenResponse(**token_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/plaid/exchange_token", response_model=PlaidExchangeTokenResponse)
def exchange_token(
    request: PlaidExchangeTokenRequest,
    current_user: UserResponse = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    try:
        exchange_data = plaid_client.exchange_public_token(request.public_token)
        clear_demo_data(db, current_user.id)
        plaid_item = crud.upsert_plaid_item(
            db,
            user_id=current_user.id,
            item_id=exchange_data["item_id"],
            access_token=exchange_data["access_token"],
        )

        accounts = _fetch_with_retry(plaid_client.get_accounts, plaid_item.access_token)
        account_map: Dict[str, int] = {}
        for account_data in accounts:
            created_account = crud.upsert_account_from_plaid(
                db,
                current_user.id,
                plaid_item.id,
                account_data,
            )
            account_map[account_data["account_id"]] = created_account.id

        end_date = datetime.utcnow()
        latest_transaction_date = crud.get_latest_transaction_date_for_item(
            db, plaid_item.id
        )
        if latest_transaction_date:
            start_date = latest_transaction_date - timedelta(days=2)
        elif plaid_item.last_synced_at:
            start_date = plaid_item.last_synced_at - timedelta(days=2)
        else:
            start_date = end_date - timedelta(days=90)
        if start_date >= end_date:
            start_date = end_date - timedelta(days=1)
        transactions_data = _fetch_with_retry(
            plaid_client.get_transactions,
            plaid_item.access_token,
            start_date,
            end_date,
        )

        for transaction_data in transactions_data["transactions"]:
            linked_account_id = account_map.get(transaction_data.get("account_id"))
            if not linked_account_id:
                continue
            crud.upsert_transaction_from_plaid(
                db,
                current_user.id,
                linked_account_id,
                transaction_data,
            )

        crud.update_plaid_item_last_synced(db, plaid_item.id, end_date)
        crud.record_plaid_sync_event(
            db,
            current_user.id,
            plaid_item.id,
            transactions_count=len(transactions_data.get("transactions", [])),
            pages_fetched=transactions_data.get("request_count", 1),
        )

        crud.delete_insights_by_user(db, current_user.id)
        insights.InsightsEngine(db, current_user.id).generate_all_insights()
        
        return PlaidExchangeTokenResponse(**exchange_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Dashboard and insights endpoints
@app.get("/dashboard", response_model=DashboardData)
def get_dashboard(
    current_user: UserResponse = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    if (
        settings.demo_seed_enabled
        and settings.plaid_env != "production"
        and crud.count_transactions_by_user(db, current_user.id) == 0
    ):
        try:
            seed_demo_dataset(db, current_user.id)
        except Exception:
            logger.exception("Failed to seed demo data for user %s", current_user.id)
    dashboard_summary = crud.get_dashboard_summary(db, current_user.id)
    now_ts = datetime.utcnow()
    recent_transactions = crud.get_transactions_by_user(
        db,
        current_user.id,
        limit=10,
        end_date=now_ts,
    )
    
    insights_data = crud.get_all_insights_by_user(db, current_user.id)
    if not insights_data:
        try:
            insights_engine = insights.InsightsEngine(db, current_user.id)
            insights_data = insights_engine.generate_all_insights()
        except Exception:
            logger.exception("Failed to generate insights for user %s", current_user.id)
            insights_data = []
    
    return DashboardData(
        total_balance=dashboard_summary["total_balance"],
        monthly_spending=dashboard_summary["monthly_spending"],
        transaction_count=dashboard_summary["transaction_count"],
        top_categories=dashboard_summary["top_categories"],
        currency_code=dashboard_summary["currency_code"],
        recent_transactions=recent_transactions,
        insights=insights_data
    )

@app.get("/insights", response_model=InsightsResponse)
def get_insights(
    current_user: UserResponse = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    return crud.get_all_insights_by_user(db, current_user.id)

@app.get("/transactions")
def get_transactions(
    limit: int = 100,
    offset: int = 0,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: UserResponse = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    start_bound = _normalize_datetime_param(start_date)
    end_bound = _normalize_datetime_param(end_date, is_end=True)
    items = crud.get_transactions_by_user(
        db,
        current_user.id,
        limit,
        offset,
        start_date=start_bound,
        end_date=end_bound
    )
    total = crud.count_transactions_by_user(
        db,
        current_user.id,
        start_date=start_bound,
        end_date=end_bound
    )
    return {"items": items, "total": total}

@app.get("/accounts")
def get_accounts(
    current_user: UserResponse = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    return crud.get_accounts_by_user(db, current_user.id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
