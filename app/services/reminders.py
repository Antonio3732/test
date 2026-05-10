import logging
import os
import smtplib
from datetime import date, timedelta
from email.message import EmailMessage

from sqlalchemy.orm import Session

from app.models import RecurringBill, User

logger = logging.getLogger(__name__)


def send_bill_reminders(db: Session) -> int:
    tomorrow = date.today() + timedelta(days=1)
    bills = (
        db.query(RecurringBill)
        .filter(RecurringBill.due_date == tomorrow)
        .filter(RecurringBill.reminder_sent_for_due_date.is_(None))
        .all()
    )

    users = db.query(User).order_by(User.id).all()
    if not bills or not users:
        return 0

    sent_count = 0
    for bill in bills:
        if send_email(
            recipients=[user.email for user in users],
            subject=f"Bill due tomorrow: {bill.title}",
            body=(
                f"Reminder: {bill.title} is due tomorrow.\n"
                f"Amount: {bill.amount}\n"
                f"Category: {bill.category.value}\n"
            ),
        ):
            bill.reminder_sent_for_due_date = bill.due_date
            sent_count += 1

    db.commit()
    return sent_count


def send_email(recipients: list[str], subject: str, body: str) -> bool:
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    sender = os.getenv("SMTP_FROM") or username

    if not host or not sender:
        logger.warning("SMTP not configured; skipped reminder: %s", subject)
        return False

    message = EmailMessage()
    message["From"] = sender
    message["To"] = ", ".join(recipients)
    message["Subject"] = subject
    message.set_content(body)

    try:
        with smtplib.SMTP(host, port, timeout=30) as smtp:
            smtp.starttls()
            if username and password:
                smtp.login(username, password)
            smtp.send_message(message)
    except OSError as exc:
        logger.exception("Failed to send email %s: %s", subject, exc)
        return False

    return True
