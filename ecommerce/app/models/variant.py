from datetime import datetime, timezone
from typing import Optional
import uuid


def generate_variant_sku(parent_sku: str, color: str = "", attributes: dict = {}) -> str:
    parts = [parent_sku]
    if color:
        parts.append(color[:3].upper().replace(" ", ""))
    if attributes:
        for val in list(attributes.values())[:2]:
            compact = str(val).upper().replace("GB","G").replace("TB","T").replace(" ","")[:4]
            parts.append(compact)
    return "-".join(parts)


def build_variant_document(
    product_id: str,
    color: str = "",
    attributes: Optional[dict] = None,
    sku: str = "",
    selling_price: float = 0.0,
    cost_price: float = 0.0,
    stock: int = 0,
    image_metadata: Optional[list] = None,
    created_by: str = "",
) -> dict:
    
    now = datetime.now(timezone.utc)
    return {
        "variant_id": str(uuid.uuid4()),
        "product_id": product_id,          # FK reference to products collection
        "color": color.strip(),
        "attributes": attributes or {},
        "sku": sku.strip().upper(),
        "selling_price": round(selling_price, 2),
        "cost_price": round(cost_price, 2),
        "stock": max(0, stock),
        "image_metadata": image_metadata or [],
        "is_active": True,
        "created_by": created_by,
        "created_at": now,
        "updated_at": now,
    }