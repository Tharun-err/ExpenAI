from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.database import SessionLocal
from backend.app.models.transaction import Transaction
from backend.app.models.category import Category
from backend.app.models.account import Account
from backend.app.schemas.transaction import TransactionCreate


router = APIRouter(prefix="/transactions", tags=["Transactions"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _validate_references(db: Session, transaction: TransactionCreate) -> None:
    if transaction.category_id is not None:
        category = (
            db.query(Category)
            .filter(Category.id == transaction.category_id)
            .first()
        )
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")

    if transaction.account_id is not None:
        account = (
            db.query(Account)
            .filter(Account.id == transaction.account_id)
            .first()
        )
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")


def _check_duplicate(
    db: Session,
    account_id: int | None,
    external_id: str | None,
    exclude_id: int | None = None,
) -> None:
    if account_id is None or external_id is None:
        return

    query = db.query(Transaction).filter(
        Transaction.account_id == account_id,
        Transaction.external_id == external_id,
    )

    if exclude_id is not None:
        query = query.filter(Transaction.id != exclude_id)

    if query.first():
        raise HTTPException(
            status_code=409,
            detail="Duplicate transaction external_id for this account",
        )


@router.post("/")
def create_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db),
):
    _validate_references(db, transaction)
    _check_duplicate(db, transaction.account_id, transaction.external_id)

    data = transaction.model_dump()
    if data.get("transaction_date") is None:
        data.pop("transaction_date")

    new_transaction = Transaction(**data)

    try:
        db.add(new_transaction)
        db.commit()
        db.refresh(new_transaction)
    except Exception:
        db.rollback()
        raise

    return new_transaction


@router.get("/")
def get_transactions(
    account_id: int | None = None,
    category_id: int | None = None,
    transaction_type: str | None = Query(
        default=None,
        alias="type",
        pattern="^(income|expense|transfer)$",
    ),
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
):
    if start_date and end_date and end_date < start_date:
        raise HTTPException(
            status_code=400,
            detail="end_date must be on or after start_date",
        )

    query = db.query(Transaction)

    if account_id is not None:
        query = query.filter(Transaction.account_id == account_id)

    if category_id is not None:
        query = query.filter(Transaction.category_id == category_id)

    if transaction_type is not None:
        query = query.filter(Transaction.type == transaction_type)

    if start_date is not None:
        query = query.filter(Transaction.transaction_date >= start_date)

    if end_date is not None:
        query = query.filter(Transaction.transaction_date <= end_date)

    return query.order_by(
        Transaction.transaction_date.desc(),
        Transaction.id.desc(),
    ).all()


@router.put("/{transaction_id}")
def update_transaction(
    transaction_id: int,
    transaction: TransactionCreate,
    db: Session = Depends(get_db),
):
    existing = (
        db.query(Transaction)
        .filter(Transaction.id == transaction_id)
        .first()
    )

    if not existing:
        raise HTTPException(status_code=404, detail="Transaction not found")

    _validate_references(db, transaction)
    _check_duplicate(
        db,
        transaction.account_id,
        transaction.external_id,
        exclude_id=transaction_id,
    )

    for key, value in transaction.model_dump().items():
        if key == "transaction_date" and value is None:
            continue
        setattr(existing, key, value)

    try:
        db.commit()
        db.refresh(existing)
    except Exception:
        db.rollback()
        raise

    return existing


@router.delete("/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
):
    existing = (
        db.query(Transaction)
        .filter(Transaction.id == transaction_id)
        .first()
    )

    if not existing:
        raise HTTPException(status_code=404, detail="Transaction not found")

    db.delete(existing)
    db.commit()

    return {"message": "Transaction deleted successfully"}