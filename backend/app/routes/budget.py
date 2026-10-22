from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import SessionLocal
from backend.app.models.budget import Budget
from backend.app.models.category import Category
from backend.app.models.transaction import Transaction
from backend.app.schemas.budget import BudgetCreate


router = APIRouter(prefix="/budgets", tags=["Budgets"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _validate_category(db: Session, category_id: int | None) -> None:
    if category_id is None:
        return

    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")


def _with_spending(db: Session, budget: Budget):
    query = db.query(Transaction).filter(
        Transaction.type == "expense",
        Transaction.transaction_date >= budget.start_date,
        Transaction.transaction_date <= budget.end_date,
    )

    if budget.category_id is not None:
        query = query.filter(Transaction.category_id == budget.category_id)

    transactions = query.all()
    spent = sum(
        (transaction.amount for transaction in transactions),
        start=Decimal("0.00"),
    )

    return {
        "id": budget.id,
        "name": budget.name,
        "amount": budget.amount,
        "start_date": budget.start_date,
        "end_date": budget.end_date,
        "category_id": budget.category_id,
        "spent": spent,
        "remaining": budget.amount - spent,
        "over_budget": spent > budget.amount,
    }


@router.post("/", status_code=201)
def create_budget(
    budget: BudgetCreate,
    db: Session = Depends(get_db),
):
    _validate_category(db, budget.category_id)

    new_budget = Budget(**budget.model_dump())
    db.add(new_budget)
    db.commit()
    db.refresh(new_budget)

    return _with_spending(db, new_budget)


@router.get("/")
def get_budgets(db: Session = Depends(get_db)):
    budgets = db.query(Budget).order_by(Budget.start_date.desc()).all()
    return [_with_spending(db, budget) for budget in budgets]


@router.get("/{budget_id}")
def get_budget(
    budget_id: int,
    db: Session = Depends(get_db),
):
    budget = db.query(Budget).filter(Budget.id == budget_id).first()

    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    return _with_spending(db, budget)


@router.put("/{budget_id}")
def update_budget(
    budget_id: int,
    data: BudgetCreate,
    db: Session = Depends(get_db),
):
    budget = db.query(Budget).filter(Budget.id == budget_id).first()

    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    _validate_category(db, data.category_id)

    for key, value in data.model_dump().items():
        setattr(budget, key, value)

    db.commit()
    db.refresh(budget)

    return _with_spending(db, budget)


@router.delete("/{budget_id}")
def delete_budget(
    budget_id: int,
    db: Session = Depends(get_db),
):
    budget = db.query(Budget).filter(Budget.id == budget_id).first()

    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    db.delete(budget)
    db.commit()

    return {"message": "Budget deleted successfully"}