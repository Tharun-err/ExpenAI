import pandas as pd

from fastapi import APIRouter, UploadFile, File, HTTPException


router = APIRouter(prefix="/statements", tags=["Statements"])


@router.post("/upload")
async def upload_statement(file: UploadFile = File(...)):

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

    transactions = df.to_dict(orient="records")

    return {
        "filename": file.filename,
        "transaction_count": len(transactions),
        "transactions": transactions
    }