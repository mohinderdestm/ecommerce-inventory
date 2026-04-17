import uuid
from datetime import datetime
from fastapi import HTTPException
from app.db.database import product_collection
from app.modules.product_catalog.schemas import ProductUpdate


def error_response(code: str, message: str, status_code: int):
    raise HTTPException(
        status_code=status_code,
        detail={
            "error": code,
            "message": message
        }
    )


class ProductService:

    @staticmethod
    async def create_product(data: dict, user_id: str):

        if data["selling_price"] < data["cost_price"]:
            error_response(
                "INVALID_PRICE",
                "Selling price cannot be less than cost price",
                400
            )

        product = {
            "_id": str(uuid.uuid4()),
            **data,
            "status": True,
            "created_by": user_id,
            "updated_by": user_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        await product_collection.insert_one(product)

        product["id"] = product["_id"]
        del product["_id"]

        return product

    @staticmethod
    async def get_products(page: int = 1, limit: int = 10):

        skip = (page - 1) * limit

        products = []
        async for p in product_collection.find({"status": True}).skip(skip).limit(limit):
            p["id"] = p["_id"]
            del p["_id"]
            products.append(p)

        return {
            "page": page,
            "limit": limit,
            "data": products
        }

    @staticmethod
    async def update_product(product_id: str,  data: ProductUpdate, user_id: str):

        existing = await product_collection.find_one({"_id": product_id})

        if not existing:
            error_response("NOT_FOUND", "Product not found", 404)

        data["updated_by"] = user_id
        data["updated_at"] = datetime.utcnow()

        await product_collection.update_one(
            {"_id": product_id},
            {"$set": data}
        )

        return {"message": "Product updated"}

    @staticmethod
    async def delete_product(product_id: str):

        result = await product_collection.update_one(
            {"_id": product_id},
            {"$set": {"status": False}}
        )

        if result.modified_count == 0:
            error_response("NOT_FOUND", "Product not found", 404)

        return {"message": "Product deleted"}

    @staticmethod
    async def search_products(query: str):
        results = []

        async for p in product_collection.find({
            "$or": [
                {"name": {"$regex": query, "$options": "i"}},
                {"brand": {"$regex": query, "$options": "i"}}
            ]
        }):
            p["id"] = p["_id"]
            del p["_id"]
            results.append(p)

        return results

# import uuid
# from datetime import datetime
# from fastapi import HTTPException
# from app.db.database import product_collection


# class ProductService:

#     @staticmethod
#     async def create_product(data: dict, user_id: str):

#         if data["selling_price"] < data["cost_price"]:
#             raise HTTPException(400, "Selling price cannot be less than cost price")

#         product = {
#             "_id": str(uuid.uuid4()),
#             "name": data["name"],
#             "description": data.get("description"),
#             "category_id": data["category_id"],
#             "brand": data.get("brand"),
#             "supplier_id": data["supplier_id"],
#             "cost_price": data["cost_price"],
#             "selling_price": data["selling_price"],
#             "reorder_level": data["reorder_level"],
#             "tax_percentage": data["tax_percentage"],
#             "unit": data["unit"],
#             "status": True,
#             "created_by": user_id,
#             "updated_by": user_id,
#             "created_at": datetime.utcnow(),
#             "updated_at": datetime.utcnow()
#         }

#         await product_collection.insert_one(product)

#         product["id"] = product["_id"]
#         del product["_id"]

#         return product

#     @staticmethod
#     async def get_products():
#         products = []
#         async for p in product_collection.find({"status": True}):
#             p["id"] = p["_id"]
#             del p["_id"]
#             products.append(p)
#         return products

#     @staticmethod
#     async def update_product(product_id: str, data: dict, user_id: str):

#         existing = await product_collection.find_one({"_id": product_id})
#         if not existing:
#             raise HTTPException(404, "Product not found")

#         data["updated_by"] = user_id
#         data["updated_at"] = datetime.utcnow()

#         await product_collection.update_one(
#             {"_id": product_id},
#             {"$set": data}
#         )

#         return {"message": "Updated"}

#     @staticmethod
#     async def delete_product(product_id: str):
#         await product_collection.update_one(
#             {"_id": product_id},
#             {"$set": {"status": False}}
#         )
#         return {"message": "Deleted"}

#     @staticmethod
#     async def search_products(query: str):
#         results = []
#         async for p in product_collection.find({
#             "$or": [
#                 {"name": {"$regex": query, "$options": "i"}},
#                 {"brand": {"$regex": query, "$options": "i"}}
#             ]
#         }):
#             p["id"] = p["_id"]
#             del p["_id"]
#             results.append(p)
#         return results


