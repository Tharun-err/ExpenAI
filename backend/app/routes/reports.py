from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.database import SessionLocal
from backend.app.models.transaction import Transaction
from backend.app.models.category import Category
from backend.app.models.account import Account


router = APIRouter(prefix="/reports", tags=["Financial Reports"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _date_filter(query, start_date: date | None, end_date: date | None):
    if start_date and end_date and end_date < start_date:
        raise HTTPException(
            status_code=400,
            detail="end_date must be on or after start_date",
        )

    if start_date:
        query = query.filter(Transaction.transaction_date >= start_date)

    if end_date:
        query = query.filter(Transaction.transaction_date <= end_date)

    return query


@router.get("/summary")
def financial_summary(
    start_date: date | None = None,
    end_date: date | None = None,
    account_id: int | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Transaction)
    query = _date_filter(query, start_date, end_date)

    if account_id is not None:
        query = query.filter(Transaction.account_id == account_id)

    rows = query.all()

    income = sum(
        (row.amount for row in rows if row.type == "income"),
        start=Decimal("0.00"),
    )
    expenses = sum(
        (row.amount for row in rows if row.type == "expense"),
        start=Decimal("0.00"),
    )

    return {
        "start_date": start_date,
        "end_date": end_date,
        "account_id": account_id,
        "income": income,
        "expenses": expenses,
        "net_cash_flow": income - expenses,
        "transaction_count": len(rows),
    }


@router.get("/by-category")
def spending_by_category(
    start_date: date | None = None,
    end_date: date | None = None,
    account_id: int | None = None,
    db: Session = Depends(get_db),
):
    query = (
        db.query(
            Transaction.category_id,
            Category.name,
            func.coalesce(func.sum(Transaction.amount), 0).label("total"),
            func.count(Transaction.id).label("transaction_count"),
        )
        .outerjoin(Category, Transaction.category_id == Category.id)
        .filter(Transaction.type == "expense")
    )

    query = _date_filter(query, start_date, end_date)

    if account_id is not None:
        query = query.filter(Transaction.account_id == account_id)

    rows = (
        query.group_by(Transaction.category_id, Category.name)
        .order_by(func.sum(Transaction.amount).desc())
        .all()
    )

    return [
        {
            "category_id": row.category_id,
            "category": row.name or "Uncategorized",
            "total": row.total,
            "transaction_count": row.transaction_count,
        }
        for row in rows
    ]


@router.get("/accounts")
def account_balances(db: Session = Depends(get_db)):
    accounts = db.query(Account).order_by(Account.id).all()
    output = []

    for account in accounts:
        income = (
            db.query(func.coalesce(func.sum(Transaction.amount), 0))
            .filter(
                Transaction.account_id == account.id,
                Transaction.type == "income",
            )
            .scalar()
        )

        expenses = (
            db.query(func.coalesce(func.sum(Transaction.amount), 0))
            .filter(
                Transaction.account_id == account.id,
                Transaction.type == "expense",
            )
            .scalar()
        )

        output.append(
            {
                "account_id": account.id,
                "name": account.name,
                "type": account.type,
                "opening_balance": account.balance,
                "income": income,
                "expenses": expenses,
                "calculated_balance": account.balance + income - expenses,
            }
        )

    return output