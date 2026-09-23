from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.app.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    type = Column(String, nullable=False)

    category_id = Column(
        Integer,
        ForeignKey("categories.id"),
        nullable=True
    )

    category = relationship("Category")

    account_id = Column(
        Integer,
        ForeignKey("accounts.id"),
        nullable=True
    )

    account = relationship("Account")

    created_at = Column(DateTime(timezone=True), server_default=func.now())