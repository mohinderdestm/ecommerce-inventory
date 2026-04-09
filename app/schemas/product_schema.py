from pydantic import BaseModel,Field
from typing import Optional,List,Dict, Any
from datetime import datetime

class ProductVariant(BaseModel):
    attributes: Dict[str, Any] = Field(default_factory=dict)
    sku: Optional[str] = None
    stock: int = 0
    additional_price: float = 0

class ProductCreate(BaseModel):
    name: str
    description: Optional[str]=None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    brand: Optional[str] = None
    supplier_ids: List[str] = Field(default_factory=list)
    cost_price: float
    selling_price: float =0
    reorder_level:int = 10
    tax_percentage: float = 0
    unit :str ="pcs"  
    image_url: Optional[str] = None

    variants: List[ProductVariant] = Field(default_factory=list)

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    supplier_ids: Optional[List[str]] = None
    cost_price: Optional[float] = None
    selling_price: Optional[float] = None
    reorder_level: Optional[int] = None
    tax_percentage: Optional[float] = None
    unit: Optional[str] = None
    status: Optional[str] = None
    image_url: Optional[str] = None 

    variants: Optional[List[ProductVariant]] = None  
    

class ProductResponse(BaseModel):
    id: str
    name: str
    sku: str
    category: str
    selling_price: float
    status: str
    created_at: datetime
    updated_at: datetime


