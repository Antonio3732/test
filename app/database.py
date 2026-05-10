import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models import Base, User

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./apartment_expenses.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    seed_users()


def seed_users() -> None:
    with SessionLocal() as db:
        if db.query(User).count():
            return

        db.add_all(
            [
                User(name="Alex", email="alex@example.com"),
                User(name="Ben", email="ben@example.com"),
                User(name="Chris", email="chris@example.com"),
                User(name="Daniel", email="daniel@example.com"),
            ]
        )
        db.commit()


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
