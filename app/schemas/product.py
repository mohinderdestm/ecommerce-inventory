from pydantic import BaseModel, Field
from typing import Optional, List
from app.schemas.supplier_schema import SupplierResponse


class ProductVariant(BaseModel):
    name: str
    sku: Optional[str] = None
    additional_price: float = Field(default=0.0, ge=0)
    reorder_level: int = Field(default=0, ge=0)
    stock: int = Field(default=0, ge=0)
    image: Optional[str] = None


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
    variants: List[ProductVariant] = []


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
    variants: List[dict] = []
    supplier_details: Optional[SupplierResponse] = None
