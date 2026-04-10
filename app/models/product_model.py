from datetime import datetime
import random
import string

class ProductModel:

    @staticmethod
    def generate_sku(prefix: str = "PRD") -> str:
        prefix = prefix[:3].upper() if prefix else "PRD"
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"{prefix}-{suffix}"

    @staticmethod
    def create_variant(data: dict, parent_sku: str) -> dict:
        """Create a product variant"""
        return {
            "sku": f"{parent_sku}-{data.get('name', '').upper()[:3]}{random.randint(10,99)}",
            "name": data.get("name", ""),  # e.g., "Red - Large"
            "attributes": data.get("attributes", {}),  # {"color": "Red", "size": "Large"}
            "price_adjustment": float(data.get("price_adjustment", 0)),  # +/- from base price
            "quantity": int(data.get("quantity", 0)),
            "image_url": data.get("image_url", ""),
            "status": data.get("status", "active")
        }

    @staticmethod
    def create(data: dict, image_url: str, user_id: str) -> dict:
        return {
            "name": data["name"],
            "sku": data.get("sku") or ProductModel.generate_sku(data.get("category", "")),
            "description": data.get("description", ""),
            "category_id": data.get("category_id"),
            "subcategory_id": data.get("subcategory_id"),
            "brand": data.get("brand", ""),
            "supplier_id": data.get("supplier_id"),  # Primary supplier
            "cost_price": float(data.get("cost_price", 0)),
            "selling_price": float(data.get("selling_price", 0)),
            "quantity": int(data.get("quantity", 0)),
            "reorder_level": int(data.get("reorder_level", 10)),
            "tax_percentage": float(data.get("tax_percentage", 0)),
            "unit": data.get("unit", "pcs"),
            "status": data.get("status", "active"),
            "image_url": image_url,
            "variants": [],  # List of variants
            "tags": data.get("tags", []),
            "created_by": user_id,
            "updated_by": user_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }