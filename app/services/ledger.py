from decimal import Decimal

from app.models import Expense, User
from app.schemas import SettlementOut


def decimal_to_cents(value: Decimal) -> int:
    return int((value * Decimal("100")).quantize(Decimal("1")))


def cents_to_decimal(value: int) -> Decimal:
    return (Decimal(value) / Decimal("100")).quantize(Decimal("0.01"))


def calculate_settlements(users: list[User], expenses: list[Expense]) -> list[SettlementOut]:
    balances = {user.id: 0 for user in users}
    user_by_id = {user.id: user for user in users}

    for expense in expenses:
        participants = sorted(expense.participants, key=lambda user: user.id)
        if not participants:
            continue

        total_cents = decimal_to_cents(expense.amount)
        base_share = total_cents // len(participants)
        remainder = total_cents % len(participants)

        balances[expense.paid_by_user_id] += total_cents

        for index, participant in enumerate(participants):
            share = base_share + (1 if index < remainder else 0)
            balances[participant.id] -= share

    debtors = [[user_id, -balance] for user_id, balance in balances.items() if balance < 0]
    creditors = [[user_id, balance] for user_id, balance in balances.items() if balance > 0]

    debtors.sort(key=lambda item: item[0])
    creditors.sort(key=lambda item: item[0])

    settlements: list[SettlementOut] = []
    debtor_index = 0
    creditor_index = 0

    while debtor_index < len(debtors) and creditor_index < len(creditors):
        debtor_id, debt_amount = debtors[debtor_index]
        creditor_id, credit_amount = creditors[creditor_index]
        amount = min(debt_amount, credit_amount)

        settlements.append(
            SettlementOut(
                from_user_id=debtor_id,
                from_user_name=user_by_id[debtor_id].name,
                to_user_id=creditor_id,
                to_user_name=user_by_id[creditor_id].name,
                amount=cents_to_decimal(amount),
            )
        )

        debtors[debtor_index][1] -= amount
        creditors[creditor_index][1] -= amount

        if debtors[debtor_index][1] == 0:
            debtor_index += 1
        if creditors[creditor_index][1] == 0:
            creditor_index += 1

    return settlements
