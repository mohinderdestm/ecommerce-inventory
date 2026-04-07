import uuid
from datetime import datetime
from app.db.database import variant_collection, product_collection
from app.modules.product_catalog.utils import generate_sku


class VariantService:

    @staticmethod
    async def create_variant(product_id: str, data: dict):

        product = await product_collection.find_one({"_id": product_id})
        if not product:
            raise Exception("Product not found")

        sku = generate_sku(
            product["category_id"],
            product["name"],
            data.get("color"),
            data.get("size")
        )

        variant = {
            "_id": str(uuid.uuid4()),
            "product_id": product_id,
            "color": data.get("color"),
            "size": data.get("size"),
            "price": data["price"],
            "stock": data["stock"],
            "sku": sku,
            "created_at": datetime.utcnow()
        }

        await variant_collection.insert_one(variant)

        variant["id"] = variant["_id"]
        del variant["_id"]

        return variant

    @staticmethod
    async def get_variants(product_id: str):
        variants = []
        async for v in variant_collection.find({"product_id": product_id}):
            v["id"] = v["_id"]
            del v["_id"]
            variants.append(v)
        return variants