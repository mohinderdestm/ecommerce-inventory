from app.core.database import db
from bson import ObjectId
from bson.errors import InvalidId
from app.models.product import product_model


class ProductRepository:
    collection = db["products"]

    @classmethod
    async def create_product(cls, data: dict):

        result = await cls.collection.insert_one(data)

        return await cls.get_product_by_id(str(result.inserted_id))

    @classmethod
    async def get_all_products(cls):

        pipeline = [
            {
                "$lookup": {
                    "from": "suppliers",
                    "localField": "supplier_email",
                    "foreignField": "email",
                    "as": "supplier_details",
                }
            }
        ]

        products = []
        async for product in cls.collection.aggregate(pipeline):
            products.append(product_model(product))
        return products

    @classmethod
    async def get_product_by_id(cls, product_id: str):

        try:
            obj_id = ObjectId(product_id)
        except InvalidId:
            return None

        pipeline = [
            {"$match": {"_id": obj_id}},
            {
                "$lookup": {
                    "from": "suppliers",
                    "localField": "supplier_email",
                    "foreignField": "email",
                    "as": "supplier_details",
                }
            },
        ]

        cursor = cls.collection.aggregate(pipeline)

        product_list = await cursor.to_list(length=1)

        if not product_list:
            return None

        return product_model(product_list[0])

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
