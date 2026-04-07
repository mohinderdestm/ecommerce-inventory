from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from app.models.product import ProductStatus, ProductUnit


# Image Metadata

class ImageMetadata(BaseModel):
    url: str = Field(..., examples=["https://cdn.example.com/product.jpg"])
    alt_text: Optional[str] = Field(default="", examples=["Front view of product"])
    is_primary: bool = Field(default=False)


# Category Schemas

class CategoryCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, examples=["Electronics"])
    description: Optional[str] = Field(default="", max_length=500)
    parent_id: Optional[str] = Field(
        default=None,
        description="ID of parent category. Leave empty for top-level category.",
        examples=[None]
    )


class CategoryUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    is_active: Optional[bool] = None


class CategoryResponse(BaseModel):
    id: str = Field(..., alias="_id")
    name: str
    slug: str
    description: str
    parent_id: Optional[str] = None
    is_active: bool
    created_by: str
    created_at: datetime

    model_config = {"populate_by_name": True}


# Product Schemas

class ProductCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=200, examples=["Nike Air Max 90"])
    description: Optional[str] = Field(default="", max_length=2000)
    category_id: str = Field(..., description="MongoDB ObjectId of the category")
    brand: Optional[str] = Field(default="", max_length=100, examples=["Nike"])
    supplier_ids: Optional[list[str]] = Field(
        default=[],
        description="List of supplier MongoDB ObjectIds"
    )
    cost_price: float = Field(..., gt=0, examples=[800.00])
    selling_price: float = Field(..., gt=0, examples=[1200.00])
    reorder_level: int = Field(default=0, ge=0, examples=[10])
    tax_percentage: float = Field(default=0.0, ge=0, le=100, examples=[18.0])
    unit: ProductUnit = Field(default=ProductUnit.PIECE)
    status: ProductStatus = Field(default=ProductStatus.ACTIVE)
    image_metadata: Optional[list[ImageMetadata]] = Field(default=[])

    # Optional: override auto-generated SKU
    sku: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Leave empty to auto-generate SKU"
    )

    @field_validator("selling_price")
    @classmethod
    def selling_price_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Selling price must be greater than 0.")
        return round(v, 2)

    @field_validator("cost_price")
    @classmethod
    def cost_price_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Cost price must be greater than 0.")
        return round(v, 2)


class ProductUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    category_id: Optional[str] = None
    brand: Optional[str] = Field(default=None, max_length=100)
    supplier_ids: Optional[list[str]] = None
    cost_price: Optional[float] = Field(default=None, gt=0)
    selling_price: Optional[float] = Field(default=None, gt=0)
    reorder_level: Optional[int] = Field(default=None, ge=0)
    tax_percentage: Optional[float] = Field(default=None, ge=0, le=100)
    unit: Optional[ProductUnit] = None
    status: Optional[ProductStatus] = None
    image_metadata: Optional[list[ImageMetadata]] = None


class ProductResponse(BaseModel):
    id: str = Field(..., alias="_id")
    name: str
    sku: str
    description: str
    category_id: str
    brand: str
    supplier_ids: list[str]
    cost_price: float
    selling_price: float
    reorder_level: int
    tax_percentage: float
    unit: str
    status: str
    image_metadata: list[ImageMetadata]
    created_by: str
    updated_by: str
    created_at: datetime
    updated_at: datetime

    model_config = {"populate_by_name": True}


class ProductListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    products: list[ProductResponse]


# Standard Response

class APIResponse(BaseModel):
    success: bool
    message: str