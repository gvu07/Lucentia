from pydantic import BaseModel, EmailStr, validator
from pydantic import ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal

# User schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Account schemas
class AccountBase(BaseModel):
    plaid_account_id: str
    name: str
    official_name: Optional[str] = None
    type: str
    subtype: Optional[str] = None
    available_balance: Optional[Decimal] = None
    current_balance: Optional[Decimal] = None
    currency_code: str = "USD"

class AccountCreate(AccountBase):
    user_id: int

class AccountResponse(AccountBase):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Transaction schemas
class TransactionBase(BaseModel):
    plaid_transaction_id: str
    amount: Decimal
    currency_code: str = "USD"
    date: datetime
    name: str
    merchant_name: Optional[str] = None
    category_primary: Optional[str] = None
    category_detailed: Optional[str] = None
    category_confidence_level: Optional[str] = None
    payment_channel: Optional[str] = None
    payment_metadata: Optional[str] = None
    location_city: Optional[str] = None
    location_region: Optional[str] = None
    location_country: Optional[str] = None
    is_pending: bool = False
    is_recurring: bool = False

class TransactionCreate(TransactionBase):
    user_id: int
    account_id: int

class TransactionResponse(TransactionBase):
    id: int
    user_id: int
    account_id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Insight schemas
class InsightBase(BaseModel):
    domain: str
    family: str
    title: str
    description: str
    data: Optional[str] = None
    priority: str = "medium"
    expires_at: Optional[datetime] = None

class InsightCreate(InsightBase):
    user_id: int

class InsightResponse(InsightBase):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class InsightFamilyGroup(BaseModel):
    key: str
    name: str
    description: Optional[str] = None
    insights: List[InsightResponse]

class InsightDomainGroup(BaseModel):
    key: str
    name: str
    description: Optional[str] = None
    families: List[InsightFamilyGroup]

# Plaid schemas
class PlaidLinkTokenResponse(BaseModel):
    link_token: str
    expiration: datetime

class PlaidExchangeTokenRequest(BaseModel):
    public_token: str

class PlaidExchangeTokenResponse(BaseModel):
    access_token: str
    item_id: str

# Insights response
class InsightsResponse(BaseModel):
    domains: List[InsightDomainGroup]

# Dashboard data
class DashboardData(BaseModel):
    total_balance: Decimal
    monthly_spending: Decimal
    transaction_count: int
    top_categories: Dict[str, Decimal]
    currency_code: str = "USD"
    recent_transactions: List[TransactionResponse]
    insights: InsightsResponse
