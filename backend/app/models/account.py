from sqlalchemy import Column, Integer, String, Numeric

from backend.app.database import Base


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    balance = Column(Numeric(12, 2), nullable=False, default=0)