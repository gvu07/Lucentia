from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, Session, create_engine, select
from datetime import date, timedelta
import plaid
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
from plaid.model.webhook_type import WebhookType

from .settings import get_settings
from .models import User, Item, Account, Transaction
from .insights import dining_trend

# initialize app
app = FastAPI(title="Lucentia API")

# enable frontend calls
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# database connection
settings = get_settings()
engine = create_engine(settings.DATABASE_URL, echo=False)

def get_session():
    with Session(engine) as session:
        yield session

# plaid client
configuration = plaid.Configuration(
    host={
        "sandbox": "https://sandbox.plaid.com",
        "development": "https://development.plaid.com",
        "production": "https://production.plaid.com",
    }[settings.PLAID_ENV],
    api_key={
        "clientId": settings.PLAID_CLIENT_ID,
        "secret": settings.PLAID_SECRET,
    },
)




api_client = plaid.ApiClient(configuration)
plaid_client = plaid_api.PlaidApi(api_client)

@app.get("/health")
def health_check():
    return {"ok": True}

@app.post("/link/token/create")
def create_link_token(session: Session = Depends(get_session), user_email: str = "demo@example.com"):
    user = session.exec(select(User).where(User.email == user_email)).first()
    if not user:
        user = User(email=user_email)
        session.add(user)
        session.commit()
        session.refresh(user)

    req = LinkTokenCreateRequest(
        user={"client_user_id": str(user.id)},
        client_name="Lucentia",
        products=[Products("transactions")],
        country_codes=[CountryCode("US")],
        language="en",
        webhook="https://example.com/webhook"  # replace later
    )

    try:
        resp = plaid_client.link_token_create(req)
        return {"link_token": resp.to_dict()["link_token"]}
    except Exception as e:
        print("🚨 Plaid Link Token Error:", e)
        raise HTTPException(status_code=500, detail=str(e))


from plaid.model.accounts_get_request import AccountsGetRequest

@app.post("/plaid/exchange_public_token")
def exchange_public_token(payload: dict, session: Session = Depends(get_session)):
    public_token = payload.get("public_token")
    user_email = payload.get("user_email", "demo@example.com")

    if not public_token:
        raise HTTPException(400, "public_token required")

    exchange_req = ItemPublicTokenExchangeRequest(public_token=public_token)
    exchange_resp = plaid_client.item_public_token_exchange(exchange_req)
    access_token = exchange_resp.to_dict()["access_token"]
    item_id = exchange_resp.to_dict()["item_id"]

    user = session.exec(select(User).where(User.email == user_email)).first()
    item = Item(plaid_item_id=item_id, access_token=access_token, user_id=user.id)
    session.add(item)
    session.commit()
    session.refresh(item)

    acc_req = AccountsGetRequest(access_token=access_token)
    accs = plaid_client.accounts_get(acc_req).to_dict()["accounts"]
    for a in accs:
        account = Account(
            item_id=item.id,
            plaid_account_id=a["account_id"],
            name=a.get("name"),
            mask=a.get("mask"),
            official_name=a.get("official_name"),
            type=a.get("type"),
            subtype=a.get("subtype"),
        )
        session.add(account)
    session.commit()
    return {"ok": True}

def upsert_transactions(session: Session, access_token: str, start_date: date, end_date: date):
    req = TransactionsGetRequest(
        access_token=access_token,
        start_date=start_date,
        end_date=end_date,
        options=TransactionsGetRequestOptions(count=100, offset=0),
    )
    resp = plaid_client.transactions_get(req).to_dict()
    txs = resp["transactions"]

    accounts = {a.plaid_account_id: a for a in session.exec(select(Account)).all()}

    for t in txs:
        acct = accounts.get(t["account_id"])
        if not acct:
            continue

        exists = session.exec(
            select(Transaction).where(Transaction.plaid_tx_id == t["transaction_id"])
        ).first()

        if not exists:
            # handle Plaid SDK returning either str or datetime.date
            tx_date = t.get("date")
            if not isinstance(tx_date, str):
                tx_date = tx_date.isoformat()

            session.add(Transaction(
                account_id=acct.id,
                plaid_tx_id=t["transaction_id"],
                date=date.fromisoformat(tx_date),
                name=t.get("name") or "",
                amount=abs(float(t["amount"])),
                merchant_name=t.get("merchant_name"),
                category=(t.get("category") or [None, None])[0],
                subcategory=(t.get("category") or [None, None])[1] if t.get("category") else None,
                iso_currency_code=t.get("iso_currency_code"),
                pending=t.get("pending"),
            ))

    session.commit()


@app.post("/plaid/backfill")
def manual_backfill(days: int = 365, session: Session = Depends(get_session)):
    for item in session.exec(select(Item)).all():
        upsert_transactions(session, item.access_token, date.today()-timedelta(days=days), date.today())
    return {"ok": True}

@app.post("/webhook")
async def webhook(request: Request, session: Session = Depends(get_session)):
    body = await request.json()
    wtype = body.get("webhook_type")
    wcode = body.get("webhook_code")
    if wtype == WebhookType("TRANSACTIONS"):
        for item in session.exec(select(Item)).all():
            upsert_transactions(session, item.access_token, date.today()-timedelta(days=30), date.today())
    return {"ok": True}

@app.get("/insights/weekly-dining")
def weekly_dining(session: Session = Depends(get_session)):
    return dining_trend(session)
