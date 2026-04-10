from datetime import datetime
from typing import Optional

class CategoryModel:

    @staticmethod
    def create(data: dict, user_id: str) -> dict:
        return {
            "name": data["name"],
            "slug": data.get("slug") or CategoryModel.generate_slug(data["name"]),
            "description": data.get("description", ""),
            "parent_id": data.get("parent_id"),  # For subcategories
            "image_url": data.get("image_url", ""),
            "status": data.get("status", "active"),  # active, inactive
            "created_by": user_id,
            "updated_by": user_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

    @staticmethod
    def generate_slug(name: str) -> str:
        import re
        slug = name.lower().strip()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug