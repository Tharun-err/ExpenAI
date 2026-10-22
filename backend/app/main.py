from fastapi import FastAPI

# Import models so SQLAlchemy registers their tables.
from backend.app.models.transaction import Transaction
from backend.app.models.account import Account
from backend.app.models.category import Category
from backend.app.models.budget import Budget

from backend.app.routes.transaction import router as transaction_router
from backend.app.routes.account import router as account_router
from backend.app.routes.category import router as category_router
from backend.app.routes.statement import router as statement_router
from backend.app.routes.budget import router as budget_router
from backend.app.routes.reports import router as reports_router


app = FastAPI(
    title="ExpenAI API",
    version="0.2.0",
)

app.include_router(transaction_router)
app.include_router(account_router)
app.include_router(category_router)
app.include_router(statement_router)
app.include_router(budget_router)
app.include_router(reports_router)


@app.get("/")
def root():
    return {"message": "ExpenAI API is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}