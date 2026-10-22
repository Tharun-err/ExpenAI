from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class BudgetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    start_date: date
    end_date: date
    category_id: int | None = None

    @model_validator(mode="after")
    def validate_budget(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")

        self.name = self.name.strip()
        if not self.name:
            raise ValueError("Budget name cannot be blank")

        return self


class BudgetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    amount: Decimal
    start_date: date
    end_date: date
    category_id: int | None = None