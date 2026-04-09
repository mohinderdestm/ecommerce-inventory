from pydantic import BaseModel, Field
from typing import Optional


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=2)
    description: Optional[str] = None
    category: str
    brand: Optional[str] = None
    cost_price: float = Field(..., gt=0)
    selling_price: float = Field(..., gt=0)
    reorder_level: int = Field(default=0, ge=0)
    tax: float = Field(default=0, ge=0)
    unit: str = Field(default="piece")
    image: Optional[str] = None


class ProductResponse(BaseModel):
    id: str
    name: str
    sku: str
    category: str
    brand: Optional[str] = None
    cost_price: float
    selling_price: float
    reorder_level: int
    tax: float
    unit: str
    description: Optional[str] = None
    status: str
    image: Optional[str] = None
