import random
import string
import asyncio
from fastapi import HTTPException
from app.repositories.product_repository import ProductRepository
from app.core.websocket_manager import manager


class ProductService:

    @staticmethod
    def generate_sku():
        return "PROD-" + "".join(
            random.choices(string.ascii_uppercase + string.digits, k=6)
        )

    @classmethod
    async def create_product(cls, data: dict, user: dict):
        data["sku"] = cls.generate_sku()
        data["status"] = "active"
        data["created_by"] = user.get("id")

        if "image" not in data:
            data["image"] = None

        product = await ProductRepository.create_product(data)

        asyncio.create_task(
            manager.broadcast({"event": "PRODUCT_CREATED", "data": product})
        )

        return product

    @classmethod
    async def get_products(cls):
        return await ProductRepository.get_all_products()

    @classmethod
    async def update_product(cls, product_id: str, data: dict):
        result = await ProductRepository.update_product(product_id, data)

        if not result or result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Product not found")

        updated_product = await ProductRepository.get_product_by_id(product_id)

        asyncio.create_task(
            manager.broadcast({"event": "PRODUCT_UPDATED", "data": updated_product})
        )

        return {"message": "Product updated"}

    @classmethod
    async def delete_product(cls, product_id: str):
        result = await ProductRepository.delete_product(product_id)

        if not result or result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Product not found")

        asyncio.create_task(
            manager.broadcast({"event": "PRODUCT_DELETED", "data": {"id": product_id}})
        )

        return {"message": "Product deleted successfully"}
