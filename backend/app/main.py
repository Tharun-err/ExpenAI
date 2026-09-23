from fastapi import FastAPI

from backend.app.database import Base, engine
from backend.app.models.transaction import Transaction
from backend.app.models.account import Account
from backend.app.models.category import Category
from backend.app.routes.transaction import router as transaction_router
from backend.app.routes.account import router as account_router
from backend.app.routes.category import router as category_router

Base.metadata.create_all(bind=engine)


app = FastAPI()


app.include_router(transaction_router)
app.include_router(account_router)
app.include_router(category_router)

@app.get("/")
def root():
    return {"message": "AI Finance Controller API is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}