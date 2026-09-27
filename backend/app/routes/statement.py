import pandas as pd

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session

from backend.app.database import SessionLocal
from backend.app.models.transaction import Transaction


router = APIRouter(prefix="/statements", tags=["Statements"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/upload")
async def upload_statement(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are supported"
        )

    try:
        df = pd.read_csv(file.file)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Could not read CSV file"
        )

    required_columns = {
        "date",
        "description",
        "amount",
        "type"
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise HTTPException(
            status_code=400,
            detail=f"Missing columns: {list(missing_columns)}"
        )

    imported_transactions = []

    for _, row in df.iterrows():

        transaction = Transaction(
            description=str(row["description"]),
            amount=float(row["amount"]),
            type=str(row["type"])
        )

        db.add(transaction)
        imported_transactions.append(transaction)

    db.commit()

    for transaction in imported_transactions:
        db.refresh(transaction)

    return {
        "filename": file.filename,
        "transaction_count": len(imported_transactions),
        "message": "Transactions imported successfully"
    }