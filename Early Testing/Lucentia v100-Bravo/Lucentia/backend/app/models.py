from sqlalchemy import Column, Integer, String, DateTime, Numeric, Text, Boolean, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    plaid_access_token = Column(String, nullable=True)
    plaid_item_id = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    accounts = relationship("Account", back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    plaid_items = relationship("PlaidItem", back_populates="user", cascade="all, delete-orphan")
    plaid_sync_events = relationship("PlaidSyncEvent", back_populates="user", cascade="all, delete-orphan")

class PlaidItem(Base):
    __tablename__ = "plaid_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    item_id = Column(String, unique=True, index=True, nullable=False)
    access_token = Column(String, nullable=False)
    institution_name = Column(String, nullable=True)
    webhook_status = Column(String, nullable=True)
    last_synced_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="plaid_items")
    accounts = relationship("Account", back_populates="plaid_item")
    sync_events = relationship("PlaidSyncEvent", back_populates="plaid_item", cascade="all, delete-orphan")

class Account(Base):
    __tablename__ = "accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plaid_item_id = Column(Integer, ForeignKey("plaid_items.id"), nullable=True)
    plaid_account_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    official_name = Column(String, nullable=True)
    type = Column(String, nullable=False)
    subtype = Column(String, nullable=True)
    available_balance = Column(Numeric(15, 2), nullable=True)
    current_balance = Column(Numeric(15, 2), nullable=True)
    currency_code = Column(String, default="USD")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="accounts")
    plaid_item = relationship("PlaidItem", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    plaid_transaction_id = Column(String, unique=True, index=True, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    currency_code = Column(String, default="USD")
    date = Column(DateTime, nullable=False)
    name = Column(String, nullable=False)
    merchant_name = Column(String, nullable=True)
    category_primary = Column(String, nullable=True)
    category_detailed = Column(String, nullable=True)
    category_confidence_level = Column(String, nullable=True)
    payment_channel = Column(String, nullable=True)
    payment_metadata = Column(Text, nullable=True)
    location_city = Column(String, nullable=True)
    location_region = Column(String, nullable=True)
    location_country = Column(String, nullable=True)
    is_pending = Column(Boolean, default=False)
    is_recurring = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="transactions")
    account = relationship("Account", back_populates="transactions")
    
    __table_args__ = (
        Index("idx_transaction_user_date", "user_id", "date"),
        Index("idx_transaction_category", "user_id", "category_primary"),
    )

class Insight(Base):
    __tablename__ = "insights"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category = Column(String, nullable=False)  # dining, financial_health, merchant, etc.
    type = Column(String, nullable=False)  # insight_type: spending_increase, recommendation, etc.
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    data = Column(Text, nullable=True)  # JSON string with supporting data
    priority = Column(String, default="medium")  # high, medium, low
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index("idx_insight_user_active", "user_id", "is_active"),
        Index("idx_insight_category", "user_id", "category"),
    )

class PlaidSyncEvent(Base):
    __tablename__ = "plaid_sync_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plaid_item_id = Column(Integer, ForeignKey("plaid_items.id"), nullable=False)
    event_type = Column(String, nullable=False, default="exchange")
    transactions_count = Column(Integer, default=0)
    pages_fetched = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="plaid_sync_events")
    plaid_item = relationship("PlaidItem", back_populates="sync_events")
