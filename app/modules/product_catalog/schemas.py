from pydantic import BaseModel
from typing import Optional

class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category_id: str
    brand: Optional[str] = None
    supplier_id: str
    cost_price: float
    selling_price: float
    reorder_level: int
    tax_percentage: float
    unit: str


class VariantCreate(BaseModel):
    color: Optional[str]
    size: Optional[str]
    price: float
    stock: int


class ProductUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    selling_price: Optional[float]
    brand: Optional[str]