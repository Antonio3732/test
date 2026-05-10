from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models import ExpenseCategory


class UserOut(BaseModel):
    id: int
    name: str
    email: str

    model_config = {"from_attributes": True}


class ExpenseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    amount: Decimal = Field(gt=0)
    category: ExpenseCategory
    paid_by_user_id: int
    split_between_user_ids: list[int] = Field(min_length=1)


class ExpenseOut(BaseModel):
    id: int
    title: str
    amount: Decimal
    category: ExpenseCategory
    paid_by_user_id: int
    split_between_user_ids: list[int]
    created_at: datetime


class SettlementOut(BaseModel):
    from_user_id: int
    from_user_name: str
    to_user_id: int
    to_user_name: str
    amount: Decimal


class RecurringBillCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    amount: Decimal = Field(gt=0)
    category: ExpenseCategory
    due_date: date
    paid_by_user_id: int | None = None


class RecurringBillOut(BaseModel):
    id: int
    title: str
    amount: Decimal
    category: ExpenseCategory
    due_date: date
    paid_by_user_id: int | None
    reminder_sent_for_due_date: date | None

    model_config = {"from_attributes": True}
