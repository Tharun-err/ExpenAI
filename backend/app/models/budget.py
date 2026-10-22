from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    Date,
    ForeignKey,
    CheckConstraint,
)
from sqlalchemy.orm import relationship

from backend.app.database import Base


class Budget(Base):
    __tablename__ = "budgets"

    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_budget_amount_positive"),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    category = relationship("Category")