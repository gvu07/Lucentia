# backend/app/schemas.py

from pydantic import BaseModel
from datetime import date
from typing import Optional

class UserBase(BaseModel):
    email: str

class UserRead(UserBase):
    id: int

class ItemBase(BaseModel):
    plaid_item_id: str

class AccountBase(BaseModel):
    name: Optional[str]
    type: Optional[str]
    subtype: Optional[str]

class TransactionBase(BaseModel):
    date: date
    name: str
    amount: float
    merchant_name: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
