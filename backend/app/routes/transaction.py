from fastapi import APIRouter, Depends, HTTPException
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


@router.post("/")
def create_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db)
):
    if transaction.category_id is not None:
        category = (
            db.query(Category)
            .filter(Category.id == transaction.category_id)
            .first()
        )

        if not category:
            raise HTTPException(
                status_code=404,
                detail="Category not found"
            )

    if transaction.account_id is not None:
        account = (
            db.query(Account)
            .filter(Account.id == transaction.account_id)
            .first()
        )

        if not account:
            raise HTTPException(
                status_code=404,
                detail="Account not found"
            )

    new_transaction = Transaction(
        description=transaction.description,
        amount=transaction.amount,
        type=transaction.type,
        category_id=transaction.category_id,
        account_id=transaction.account_id
    )

    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)

    return new_transaction


@router.get("/")
def get_transactions(db: Session = Depends(get_db)):
    return db.query(Transaction).all()


@router.put("/{transaction_id}")
def update_transaction(
    transaction_id: int,
    transaction: TransactionCreate,
    db: Session = Depends(get_db)
):
    existing_transaction = (
        db.query(Transaction)
        .filter(Transaction.id == transaction_id)
        .first()
    )

    if not existing_transaction:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    if transaction.category_id is not None:
        category = (
            db.query(Category)
            .filter(Category.id == transaction.category_id)
            .first()
        )

        if not category:
            raise HTTPException(
                status_code=404,
                detail="Category not found"
            )

    if transaction.account_id is not None:
        account = (
            db.query(Account)
            .filter(Account.id == transaction.account_id)
            .first()
        )

        if not account:
            raise HTTPException(
                status_code=404,
                detail="Account not found"
            )

    existing_transaction.description = transaction.description
    existing_transaction.amount = transaction.amount
    existing_transaction.type = transaction.type
    existing_transaction.category_id = transaction.category_id
    existing_transaction.account_id = transaction.account_id

    db.commit()
    db.refresh(existing_transaction)

    return existing_transaction


@router.delete("/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db)
):
    existing_transaction = (
        db.query(Transaction)
        .filter(Transaction.id == transaction_id)
        .first()
    )

    if not existing_transaction:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    db.delete(existing_transaction)
    db.commit()

    return {"message": "Transaction deleted successfully"}