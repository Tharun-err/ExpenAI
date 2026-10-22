from decimal import Decimal, InvalidOperation
import io

import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session

from backend.app.database import SessionLocal
from backend.app.models.transaction import Transaction
from backend.app.models.account import Account
from backend.app.models.category import Category


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
    account_id: int | None = None,
    db: Session = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are supported",
        )

    if account_id is not None:
        account = db.query(Account).filter(Account.id == account_id).first()
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")

    try:
        content = await file.read()

        if not content:
            raise ValueError("Empty file")

        df = pd.read_csv(io.BytesIO(content))
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Could not read CSV file",
        )

    df.columns = [str(column).strip().lower() for column in df.columns]

    required = {"date", "description", "amount", "type"}
    missing = required - set(df.columns)

    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing columns: {sorted(missing)}",
        )

    if df.empty:
        return {
            "filename": file.filename,
            "transaction_count": 0,
            "duplicate_count": 0,
            "message": "CSV contains no transactions",
        }

    imported = []
    duplicates = 0
    errors = []
    seen_in_file = set()

    for index, row in df.iterrows():
        line = int(index) + 2

        try:
            description = str(row["description"]).strip()

            if not description or description.lower() == "nan":
                raise ValueError("description is required")

            transaction_type = str(row["type"]).strip().lower()

            if transaction_type not in {"income", "expense", "transfer"}:
                raise ValueError(
                    "type must be income, expense, or transfer"
                )

            transaction_date = pd.to_datetime(
                row["date"],
                errors="raise",
            ).date()

            amount = Decimal(str(row["amount"])).quantize(
                Decimal("0.01")
            )

            if not amount.is_finite() or amount <= 0:
                raise ValueError("amount must be a positive number")

            external_id = None
            if "external_id" in df.columns and pd.notna(row.get("external_id")):
                external_id = str(row["external_id"]).strip() or None

            category_id = None
            if "category_id" in df.columns and pd.notna(row.get("category_id")):
                category_id = int(row["category_id"])

                category = (
                    db.query(Category)
                    .filter(Category.id == category_id)
                    .first()
                )

                if not category:
                    raise ValueError(
                        f"category_id {category_id} does not exist"
                    )

            if external_id and account_id is not None:
                key = (account_id, external_id)

                already_exists = db.query(Transaction).filter(
                    Transaction.account_id == account_id,
                    Transaction.external_id == external_id,
                ).first()

                if key in seen_in_file or already_exists:
                    duplicates += 1
                    continue

                seen_in_file.add(key)

            imported.append(
                Transaction(
                    description=description,
                    amount=amount,
                    type=transaction_type,
                    transaction_date=transaction_date,
                    external_id=external_id,
                    category_id=category_id,
                    account_id=account_id,
                )
            )

        except (
            ValueError,
            TypeError,
            InvalidOperation,
            OverflowError,
        ) as exc:
            errors.append({"row": line, "error": str(exc)})

    if errors:
        raise HTTPException(
            status_code=422,
            detail={
                "message": (
                    "CSV validation failed; "
                    "no transactions were imported"
                ),
                "errors": errors[:50],
            },
        )

    try:
        db.add_all(imported)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                "Import failed due to a database constraint; "
                "no transactions were imported"
            ),
        )

    return {
        "filename": file.filename,
        "transaction_count": len(imported),
        "duplicate_count": duplicates,
        "message": "Transactions imported successfully",
    }