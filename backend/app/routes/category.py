from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database import SessionLocal
from backend.app.models.category import Category
from backend.app.schemas.category import CategoryCreate


router = APIRouter(prefix="/categories", tags=["Categories"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/")
def create_category(
    category: CategoryCreate,
    db: Session = Depends(get_db)
):
    new_category = Category(
        name=category.name,
        type=category.type
    )

    db.add(new_category)
    db.commit()
    db.refresh(new_category)

    return new_category


@router.get("/")
def get_categories(db: Session = Depends(get_db)):
    return db.query(Category).all()


@router.put("/{category_id}")
def update_category(
    category_id: int,
    category: CategoryCreate,
    db: Session = Depends(get_db)
):
    existing_category = (
        db.query(Category)
        .filter(Category.id == category_id)
        .first()
    )

    if not existing_category:
        return {"error": "Category not found"}

    existing_category.name = category.name
    existing_category.type = category.type

    db.commit()
    db.refresh(existing_category)

    return existing_category


@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    db: Session = Depends(get_db)
):
    existing_category = (
        db.query(Category)
        .filter(Category.id == category_id)
        .first()
    )

    if not existing_category:
        return {"error": "Category not found"}

    db.delete(existing_category)
    db.commit()

    return {"message": "Category deleted successfully"}