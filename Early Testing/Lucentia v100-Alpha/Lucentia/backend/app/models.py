from datetime import date, datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str
    items: list["Item"] = Relationship(back_populates="user")

class Item(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    plaid_item_id: str
    access_token: str
    user_id: int = Field(foreign_key="user.id")
    user: Optional[User] = Relationship(back_populates="items")
    accounts: list["Account"] = Relationship(back_populates="item")

class Account(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    item_id: int = Field(foreign_key="item.id")
    plaid_account_id: str
    name: Optional[str] = None
    mask: Optional[str] = None
    official_name: Optional[str] = None
    type: Optional[str] = None
    subtype: Optional[str] = None
    item: Optional[Item] = Relationship(back_populates="accounts")
    transactions: list["Transaction"] = Relationship(back_populates="account")

class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="account.id", index=True)
    plaid_tx_id: str = Field(index=True)
    date: date
    name: str
    amount: float
    merchant_name: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    iso_currency_code: Optional[str] = None
    pending: Optional[bool] = None
    inserted_at: datetime = Field(default_factory=datetime.utcnow)
    account: Optional[Account] = Relationship(back_populates="transactions")
