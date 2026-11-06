from decimal import Decimal
from typing import Annotated, Literal
from pydantic import BaseModel, Field

Category = Literal['general', 'necklace', 'bangle', 'chain', 'ring']
Percent = Annotated[Decimal, Field(ge=0, le=10, decimal_places=2)]


class CategoryAgreements(BaseModel):
    wastage_by_category: dict[Category, Percent] = Field(min_length=1, max_length=5)
