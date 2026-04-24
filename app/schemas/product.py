from pydantic import BaseModel, Field
from typing import Optional, List
from app.schemas.supplier_schema import SupplierResponse


class WarehouseAllocation(BaseModel):
    warehouse_id: str
    quantity: int = Field(..., gt=0)


class ProductVariant(BaseModel):
    name: str
    sku: Optional[str] = None
    additional_price: float = Field(default=0.0, ge=0)
    reorder_level: int = Field(default=0, ge=0)
    stock: int = Field(default=0, ge=0)
    low_stock_threshold: int = Field(default=5, ge=0)
    expiry_date: Optional[str] = None
    image: Optional[str] = None
    warehouse_allocations: List[WarehouseAllocation] = []


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=2)
    description: Optional[str] = None
    category: str
    brand: Optional[str] = None
    cost_price: float = Field(..., gt=0)
    selling_price: float = Field(..., gt=0)
    reorder_level: int = Field(default=0, ge=0)
    low_stock_threshold: int = Field(default=5, ge=0)
    tax: float = Field(default=0, ge=0)
    unit: str = Field(default="piece")
    expiry_date: Optional[str] = None
    image: Optional[str] = None
    variants: List[ProductVariant] = []
    warehouse_allocations: List[WarehouseAllocation] = []


class ProductResponse(BaseModel):
    id: str
    name: str
    sku: str
    category: str
    brand: Optional[str] = None
    cost_price: float
    selling_price: float
    reorder_level: int
    low_stock_threshold: int = 5
    tax: float
    unit: str
    description: Optional[str] = None
    expiry_date: Optional[str] = None
    status: str
    image: Optional[str] = None
    variants: List[dict] = []
    supplier_details: Optional[SupplierResponse] = None
