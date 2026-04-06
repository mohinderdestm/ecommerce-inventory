from app.core.database import db
from bson import ObjectId
from bson.errors import InvalidId
from app.models.product import product_model


class ProductRepository:

    collection = db["products"]

    @classmethod
    async def create_product(cls, data: dict):
        result = await cls.collection.insert_one(data)

        created_product = await cls.collection.find_one({"_id": result.inserted_id})

        return product_model(created_product)

    @classmethod
    async def get_all_products(cls):
        products = []
        async for product in cls.collection.find():
            products.append(product_model(product))
        return products

    @classmethod
    async def get_product_by_id(cls, product_id: str):
        try:
            obj_id = ObjectId(product_id)
        except InvalidId:
            return None

        product = await cls.collection.find_one({"_id": obj_id})

        if not product:
            return None

        return product_model(product)

    @classmethod
    async def update_product(cls, product_id: str, data: dict):
        try:
            obj_id = ObjectId(product_id)
        except InvalidId:
            return None

        result = await cls.collection.update_one({"_id": obj_id}, {"$set": data})

        return result

    @classmethod
    async def delete_product(cls, product_id: str):
        try:
            obj_id = ObjectId(product_id)
        except InvalidId:
            return None

        result = await cls.collection.delete_one({"_id": obj_id})

        return result
