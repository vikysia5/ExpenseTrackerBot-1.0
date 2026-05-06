"""
Pydantic Models (schemas) for request/response validation
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, validator


# ============================================
# BASE
# ============================================
class TimestampMixin(BaseModel):
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ErrorResponse(BaseModel):
    detail: str
    code: Optional[str] = None


# ============================================
# USER
# ============================================
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    username: Optional[str] = None
    first_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TelegramAuth(BaseModel):
    init_data: str


class UserResponse(BaseModel):
    id: UUID
    email: Optional[str] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    telegram_id: Optional[int] = None
    avatar_url: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ============================================
# CATEGORY
# ============================================
class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    icon: str = "📦"
    color: str = "#7C3AED"
    type: str = Field(pattern="^(income|expense|both)$")


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None


class CategoryResponse(BaseModel):
    id: UUID
    name: str
    icon: str
    color: str
    type: str
    is_default: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================
# TRANSACTION
# ============================================
class TransactionCreate(BaseModel):
    type: str = Field(pattern="^(income|expense)$")
    amount: Decimal = Field(gt=0, max_digits=15, decimal_places=2)
    currency: str = "USD"
    category_id: Optional[UUID] = None
    comment: Optional[str] = None
    payment_method: str = Field(default="card", pattern="^(cash|card|crypto)$")
    transaction_date: Optional[datetime] = None
    tag_ids: Optional[List[UUID]] = []


class TransactionUpdate(BaseModel):
    type: Optional[str] = Field(None, pattern="^(income|expense)$")
    amount: Optional[Decimal] = Field(None, gt=0)
    category_id: Optional[UUID] = None
    comment: Optional[str] = None
    payment_method: Optional[str] = None
    transaction_date: Optional[datetime] = None


class TransactionResponse(BaseModel):
    id: UUID
    user_id: UUID
    type: str
    amount: Decimal
    currency: str
    comment: Optional[str] = None
    payment_method: str
    category: Optional[CategoryResponse] = None
    transaction_date: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TransactionListResponse(BaseModel):
    items: List[TransactionResponse]
    total: int
    income_total: Decimal
    expense_total: Decimal
    balance: Decimal


# ============================================
# BUDGET
# ============================================
class BudgetCreate(BaseModel):
    category_id: Optional[UUID] = None
    amount: Decimal = Field(gt=0)
    period: str = Field(default="monthly", pattern="^(weekly|monthly|yearly)$")
    start_date: str  # ISO date


class BudgetResponse(BaseModel):
    id: UUID
    category_id: Optional[UUID]
    amount: Decimal
    period: str
    start_date: str
    is_active: bool


# ============================================
# STATISTICS
# ============================================
class WeeklyStats(BaseModel):
    week: str
    income: Decimal
    expense: Decimal


class MonthlyStats(BaseModel):
    month: str
    income: Decimal
    expense: Decimal
    weeks: List[WeeklyStats] = []


class StatsResponse(BaseModel):
    total_income: Decimal
    total_expense: Decimal
    balance: Decimal
    by_category: List[dict]
    monthly: List[MonthlyStats]
