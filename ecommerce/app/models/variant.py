from datetime import datetime, timezone
from typing import Optional
import uuid


def generate_variant_sku(parent_sku: str, color: str = "", attributes: dict = {}) -> str:
    
    parts = [parent_sku]

    if color:
        # Take first 3 chars of color, uppercase
        parts.append(color[:3].upper().replace(" ", ""))

    if attributes:
        # Compact each attribute value: "128GB" -> "128G", "8GB" -> "8G"
        for val in list(attributes.values())[:2]:  # max 2 attrs in SKU
            compact = str(val).upper().replace("GB", "G").replace("TB", "T").replace(" ", "")[:4]
            parts.append(compact)

    return "-".join(parts)


def build_variant_document(
    color: str = "",
    attributes: Optional[dict] = None,
    sku: str = "",
    selling_price: float = 0.0,
    cost_price: float = 0.0,
    stock: int = 0,
    image_metadata: Optional[list] = None,
) -> dict:
    
    return {
        "variant_id": str(uuid.uuid4()),   # unique ID for this variant
        "color": color.strip(),
        "attributes": attributes or {},     # e.g. {"RAM": "8GB", "ROM": "128GB", "Size": "XL"}
        "sku": sku.strip().upper(),
        "selling_price": round(selling_price, 2),
        "cost_price": round(cost_price, 2),
        "stock": max(0, stock),             # placeholder until Module 5 (Inventory)
        "image_metadata": image_metadata or [],
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
    }