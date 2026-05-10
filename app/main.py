from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db, init_db
from app.models import Expense, RecurringBill, User
from app.schemas import ExpenseCreate, ExpenseOut, RecurringBillCreate, RecurringBillOut, SettlementOut, UserOut
from app.services.ledger import calculate_settlements
from app.services.reminders import send_bill_reminders

scheduler = BackgroundScheduler(timezone="Europe/Rome")


def run_reminder_job() -> None:
    with SessionLocal() as db:
        send_bill_reminders(db)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    if not scheduler.running:
        scheduler.add_job(run_reminder_job, "cron", hour=9, minute=0, id="daily_bill_reminders", replace_existing=True)
        scheduler.start()
    yield
    if scheduler.running:
        scheduler.shutdown()


app = FastAPI(title="Apartment Expense Manager", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).order_by(User.id).all()


@app.post("/api/expenses", response_model=ExpenseOut)
def create_expense(payload: ExpenseCreate, db: Session = Depends(get_db)):
    payer = db.get(User, payload.paid_by_user_id)
    if not payer:
        raise HTTPException(status_code=400, detail="Paid-by user does not exist")

    split_ids = list(dict.fromkeys(payload.split_between_user_ids))
    participants = db.query(User).filter(User.id.in_(split_ids)).all()
    if len(participants) != len(split_ids):
        raise HTTPException(status_code=400, detail="One or more split users do not exist")

    expense = Expense(
        title=payload.title,
        amount=payload.amount,
        category=payload.category,
        paid_by_user_id=payload.paid_by_user_id,
        participants=participants,
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)

    return serialize_expense(expense)


@app.get("/api/expenses", response_model=list[ExpenseOut])
def list_expenses(db: Session = Depends(get_db)):
    expenses = db.query(Expense).order_by(Expense.created_at.desc()).all()
    return [serialize_expense(expense) for expense in expenses]


@app.get("/api/ledger", response_model=list[SettlementOut])
def get_ledger(db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.id).all()
    expenses = db.query(Expense).all()
    return calculate_settlements(users, expenses)


@app.post("/api/recurring-bills", response_model=RecurringBillOut)
def create_recurring_bill(payload: RecurringBillCreate, db: Session = Depends(get_db)):
    if payload.paid_by_user_id and not db.get(User, payload.paid_by_user_id):
        raise HTTPException(status_code=400, detail="Paid-by user does not exist")

    bill = RecurringBill(**payload.model_dump())
    db.add(bill)
    db.commit()
    db.refresh(bill)
    return bill


@app.get("/api/recurring-bills", response_model=list[RecurringBillOut])
def list_recurring_bills(db: Session = Depends(get_db)):
    return db.query(RecurringBill).order_by(RecurringBill.due_date.asc()).all()


@app.post("/api/reminders/run")
def run_reminders_now(db: Session = Depends(get_db)):
    sent_count = send_bill_reminders(db)
    return {"sent_count": sent_count}


def serialize_expense(expense: Expense) -> ExpenseOut:
    return ExpenseOut(
        id=expense.id,
        title=expense.title,
        amount=expense.amount,
        category=expense.category,
        paid_by_user_id=expense.paid_by_user_id,
        split_between_user_ids=[user.id for user in expense.participants],
        created_at=expense.created_at,
    )


app.mount("/", StaticFiles(directory="app/static", html=True), name="static")
