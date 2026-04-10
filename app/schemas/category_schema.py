from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    slug: Optional[str] = None
    description: Optional[str] = ""
    parent_id: Optional[str] = None  # For subcategory
    image_url: Optional[str] = ""
    status: Optional[str] = "active"

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[str] = None
    image_url: Optional[str] = None
    status: Optional[str] = None

class CategoryResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: str
    parent_id: Optional[str]
    image_url: str
    status: str
    subcategories: Optional[List["CategoryResponse"]] = []
    created_at: datetime
    updated_at: datetime

class CategoryListResponse(BaseModel):
    total: int
    categories: List[CategoryResponse]