from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from app.schemas.product import ImageMetadata


class VariantCreateRequest(BaseModel):
    color: Optional[str] = Field(default="", max_length=50, examples=["Midnight Black"])
    attributes: Optional[dict] = Field(
        default={},
        examples=[{"RAM": "8GB", "ROM": "128GB"}],
        description="Key-value pairs e.g. RAM, ROM, Size, Weight"
    )
    selling_price: float = Field(..., gt=0, examples=[79999.0])
    cost_price: float = Field(..., gt=0, examples=[55000.0])
    stock: int = Field(default=0, ge=0, examples=[50])
    image_metadata: Optional[list[ImageMetadata]] = Field(default=[])
    sku: Optional[str] = Field(default=None, max_length=100)

    @field_validator("attributes")
    @classmethod
    def validate_attributes(cls, v: dict) -> dict:
        if len(v) > 10:
            raise ValueError("Maximum 10 attributes allowed per variant.")
        return v


class VariantUpdateRequest(BaseModel):
    color: Optional[str] = Field(default=None, max_length=50)
    attributes: Optional[dict] = None
    selling_price: Optional[float] = Field(default=None, gt=0)
    cost_price: Optional[float] = Field(default=None, gt=0)
    stock: Optional[int] = Field(default=None, ge=0)
    image_metadata: Optional[list[ImageMetadata]] = None
    is_active: Optional[bool] = None


class VariantBulkCreateRequest(BaseModel):
    variants: list[VariantCreateRequest] = Field(..., min_length=1, max_length=50)


class VariantResponse(BaseModel):
    id: str = Field(..., alias="_id")
    variant_id: str
    product_id: str
    color: str
    attributes: dict
    sku: str
    selling_price: float
    cost_price: float
    stock: int
    image_metadata: list[ImageMetadata]
    is_active: bool
    created_by: str
    created_at: datetime
    updated_at: datetime

    model_config = {"populate_by_name": True}


class VariantListResponse(BaseModel):
    total: int
    product_id: str
    variants: list[VariantResponse]


class APIResponse(BaseModel):
    success: bool
    message: str