from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import Column, Date, DateTime, Enum as SqlEnum, ForeignKey, Integer, Numeric, String, Table
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class ExpenseCategory(str, Enum):
    groceries = "groceries"
    rent = "rent"
    utilities = "utilities"
    internet = "internet"
    cleaning = "cleaning"
    other = "other"


expense_participants = Table(
    "expense_participants",
    Base.metadata,
    Column("expense_id", ForeignKey("expenses.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    paid_expenses: Mapped[list["Expense"]] = relationship(back_populates="payer")


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    category: Mapped[ExpenseCategory] = mapped_column(SqlEnum(ExpenseCategory), nullable=False)
    paid_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    payer: Mapped[User] = relationship(back_populates="paid_expenses")
    participants: Mapped[list[User]] = relationship(secondary=expense_participants)


class RecurringBill(Base):
    __tablename__ = "recurring_bills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    category: Mapped[ExpenseCategory] = mapped_column(SqlEnum(ExpenseCategory), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    paid_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reminder_sent_for_due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
