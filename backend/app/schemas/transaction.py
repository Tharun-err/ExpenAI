from pydantic import BaseModel


class TransactionCreate(BaseModel):
    description: str
    amount: float
    type: str
    category_id: int | None = None
    account_id: int | None = None