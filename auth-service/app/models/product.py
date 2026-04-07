from enum import Enum
from datetime import datetime, timezone
from typing import Optional


class ProductStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISCONTINUED = "discontinued"
    OUT_OF_STOCK = "out_of_stock"


class ProductUnit(str, Enum):
    PIECE = "piece"
    KG = "kg"
    GRAM = "gram"
    LITRE = "litre"
    METRE = "metre"
    BOX = "box"
    DOZEN = "dozen"
    PACK = "pack"


# Document Builders

def build_category_document(
    name: str,
    created_by: str,
    description: Optional[str] = None,
    parent_id: Optional[str] = None,
) -> dict:
    now = datetime.now(timezone.utc)
    return {
        "name": name.strip(),
        "slug": name.strip().lower().replace(" ", "-"),
        "description": description or "",
        "parent_id": parent_id,
        "is_active": True,
        "created_by": created_by,
        "updated_by": created_by,
        "created_at": now,
        "updated_at": now,
    }


def build_product_document(
    name: str,
    sku: str,
    category_id: str,
    cost_price: float,
    selling_price: float,
    created_by: str,
    description: Optional[str] = None,
    brand: Optional[str] = None,
    supplier_ids: Optional[list[str]] = None,
    reorder_level: int = 0,
    tax_percentage: float = 0.0,
    unit: str = ProductUnit.PIECE.value,
    status: str = ProductStatus.ACTIVE.value,
    image_urls: Optional[list[str]] = None,
    image_metadata: Optional[list[dict]] = None,
) -> dict:
    now = datetime.now(timezone.utc)
    return {
        "name": name.strip(),
        "sku": sku.strip().upper(),
        "description": description or "",
        "category_id": category_id,
        "brand": brand or "",
        "supplier_ids": supplier_ids or [],
        "cost_price": round(cost_price, 2),
        "selling_price": round(selling_price, 2),
        "reorder_level": reorder_level,
        "tax_percentage": round(tax_percentage, 2),
        "unit": unit,
        "status": status,
        # Image metadata
        "image_urls": image_urls or [],
        "image_metadata": image_metadata or [],
        "created_by": created_by,
        "updated_by": created_by,
        "created_at": now,
        "updated_at": now,
    }