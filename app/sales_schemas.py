from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class SaleCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=64)
    quantity: int = Field(gt=0, le=10000)
    unit_price_paise: Optional[int] = Field(default=None, ge=0, le=100000000)


class SaleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    idempotency_key: str
    sku: str
    quantity: int
    unit_price_paise: int
    total_paise: int
    created_at: datetime
