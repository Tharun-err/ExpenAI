from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import SessionLocal
from backend.app.models.account import Account
from backend.app.schemas.account import AccountCreate


router = APIRouter(prefix="/accounts", tags=["Accounts"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/")
def create_account(
    account: AccountCreate,
    db: Session = Depends(get_db)
):
    new_account = Account(
        name=account.name,
        type=account.type
    )

    db.add(new_account)
    db.commit()
    db.refresh(new_account)

    return new_account


@router.get("/")
def get_accounts(db: Session = Depends(get_db)):
    return db.query(Account).all()


@router.put("/{account_id}")
def update_account(
    account_id: int,
    account: AccountCreate,
    db: Session = Depends(get_db)
):
    existing_account = (
        db.query(Account)
        .filter(Account.id == account_id)
        .first()
    )

    if not existing_account:
        raise HTTPException(
            status_code=404,
            detail="Account not found"
        )

    existing_account.name = account.name
    existing_account.type = account.type

    db.commit()
    db.refresh(existing_account)

    return existing_account


@router.delete("/{account_id}")
def delete_account(
    account_id: int,
    db: Session = Depends(get_db)
):
    existing_account = (
        db.query(Account)
        .filter(Account.id == account_id)
        .first()
    )

    if not existing_account:
        raise HTTPException(
            status_code=404,
            detail="Account not found"
        )

    db.delete(existing_account)
    db.commit()

    return {"message": "Account deleted successfully"}