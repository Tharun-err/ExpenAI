from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    Date,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.app.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    __table_args__ = (
        UniqueConstraint(
            "account_id",
            "external_id",
            name="uq_transaction_account_external_id",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String(500), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    type = Column(String(20), nullable=False)

    transaction_date = Column(
        Date,
        nullable=False,
        server_default=func.current_date(),
    )
    external_id = Column(String(255), nullable=True)

    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    category = relationship("Category")

    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    account = relationship("Account")

    created_at = Column(
    DateTime(timezone=True),
    server_default=func.now(),
    nullable=True,
)