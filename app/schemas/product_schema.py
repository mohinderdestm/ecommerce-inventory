from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ImageMetadata(BaseModel):
    original_name: str = ""
    size: int = 0
    mime_type: str = ""
    uploaded_at: Optional[datetime] = None

class ProductCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    sku: Optional[str] = None
    description: Optional[str] = ""
    category_id: Optional[str] = None
    subcategory_id: Optional[str] = None
    brand: Optional[str] = ""
    supplier_ids: Optional[List[str]] = []
    cost_price: float = Field(..., ge=0)
    selling_price: float = Field(..., ge=0)
    quantity: int = Field(0, ge=0)
    reorder_level: int = Field(10, ge=0)
    tax_percentage: float = Field(0, ge=0, le=100)
    unit: Optional[str] = "pcs"
    status: Optional[str] = "active"
    tags: Optional[List[str]] = []

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    sku: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[str] = None
    subcategory_id: Optional[str] = None
    brand: Optional[str] = None
    supplier_ids: Optional[List[str]] = None
    cost_price: Optional[float] = None
    selling_price: Optional[float] = None
    quantity: Optional[int] = None
    reorder_level: Optional[int] = None
    tax_percentage: Optional[float] = None
    unit: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None

class ProductResponse(BaseModel):
    id: str
    name: str
    sku: str
    description: str
    category_id: Optional[str]
    subcategory_id: Optional[str]
    brand: str
    supplier_ids: List[str]
    cost_price: float
    selling_price: float
    quantity: int
    reorder_level: int
    tax_percentage: float
    unit: str
    status: str
    image_url: str
    image_metadata: ImageMetadata
    tags: List[str]
    profit_margin: Optional[float] = None
    created_by: str
    updated_by: str
    created_at: datetime
    updated_at: datetime

class ProductListResponse(BaseModel):
    total: int
    page: int
    limit: int
    products: List[ProductResponse]

class ProductSearchQuery(BaseModel):
    search: Optional[str] = None  # Search in name, sku, description
    category_id: Optional[str] = None
    subcategory_id: Optional[str] = None
    brand: Optional[str] = None
    supplier_id: Optional[str] = None
    status: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    in_stock: Optional[bool] = None
    low_stock: Optional[bool] = None  # Below reorder level
    tags: Optional[List[str]] = None