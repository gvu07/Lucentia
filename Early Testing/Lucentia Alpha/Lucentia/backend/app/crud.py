# backend/app/crud.py

from sqlmodel import Session, select
from .models import User, Item, Account, Transaction

# ---------- USER ----------
def get_user_by_email(session: Session, email: str):
    return session.exec(select(User).where(User.email == email)).first()

def create_user(session: Session, email: str) -> User:
    user = User(email=email)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

# ---------- ITEM ----------
def create_item(session: Session, user_id: int, plaid_item_id: str, access_token: str) -> Item:
    item = Item(plaid_item_id=plaid_item_id, access_token=access_token, user_id=user_id)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item

def get_items(session: Session):
    return session.exec(select(Item)).all()

# ---------- ACCOUNT ----------
def create_account(session: Session, item_id: int, account_data: dict) -> Account:
    account = Account(
        item_id=item_id,
        plaid_account_id=account_data["account_id"],
        name=account_data.get("name"),
        mask=account_data.get("mask"),
        official_name=account_data.get("official_name"),
        type=account_data.get("type"),
        subtype=account_data.get("subtype"),
    )
    session.add(account)
    session.commit()
    return account

def get_accounts_by_item(session: Session, item_id: int):
    return session.exec(select(Account).where(Account.item_id == item_id)).all()

# ---------- TRANSACTION ----------
def get_transaction_by_plaid_id(session: Session, plaid_tx_id: str):
    return session.exec(select(Transaction).where(Transaction.plaid_tx_id == plaid_tx_id)).first()

def add_transaction(session: Session, tx_data: dict, account_id: int):
    tx = Transaction(
        account_id=account_id,
        plaid_tx_id=tx_data["transaction_id"],
        date=tx_data["date"],
        name=tx_data.get("name") or "",
        amount=abs(float(tx_data["amount"])),
        merchant_name=tx_data.get("merchant_name"),
        category=(tx_data.get("category") or [None])[0],
        subcategory=(tx_data.get("category") or [None, None])[1] if tx_data.get("category") else None,
        iso_currency_code=tx_data.get("iso_currency_code"),
        pending=tx_data.get("pending"),
    )
    session.add(tx)
    session.commit()
    return tx
