import uuid
from datetime import datetime
from fastapi import HTTPException
from app.db.database import product_collection


class ProductService:

    @staticmethod
    async def create_product(data: dict, user_id: str):

        if data["selling_price"] < data["cost_price"]:
            raise HTTPException(400, "Selling price cannot be less than cost price")

        product = {
            "_id": str(uuid.uuid4()),
            "name": data["name"],
            "description": data.get("description"),
            "category_id": data["category_id"],
            "brand": data.get("brand"),
            "supplier_id": data["supplier_id"],
            "cost_price": data["cost_price"],
            "selling_price": data["selling_price"],
            "reorder_level": data["reorder_level"],
            "tax_percentage": data["tax_percentage"],
            "unit": data["unit"],
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
    async def get_products():
        products = []
        async for p in product_collection.find({"status": True}):
            p["id"] = p["_id"]
            del p["_id"]
            products.append(p)
        return products

    @staticmethod
    async def update_product(product_id: str, data: dict, user_id: str):

        existing = await product_collection.find_one({"_id": product_id})
        if not existing:
            raise HTTPException(404, "Product not found")

        data["updated_by"] = user_id
        data["updated_at"] = datetime.utcnow()

        await product_collection.update_one(
            {"_id": product_id},
            {"$set": data}
        )

        return {"message": "Updated"}

    @staticmethod
    async def delete_product(product_id: str):
        await product_collection.update_one(
            {"_id": product_id},
            {"$set": {"status": False}}
        )
        return {"message": "Deleted"}

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



# from fastapi import HTTPException
# from datetime import datetime
# import uuid
# from app.db.database import product_collection, image_collection
# from app.modules.product_catalog.utils import generate_sku


# class ProductService:

#     @staticmethod
#     async def create_product(data: dict, user_id: str):

#         if data["selling_price"] < data["cost_price"]:
#             raise HTTPException(
#                 status_code=400,
#                 detail="Selling price cannot be less than cost price"
#             )

#         sku = generate_sku(data["name"], data["category_id"])

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
#             "sku": sku,
#             "status": True,
#             "created_by": user_id,
#             "updated_by": user_id,
#             "created_at": datetime.utcnow(),
#             "updated_at": datetime.utcnow()
#         }

#         await product_collection.insert_one(product)

#         # convert _id → id
#         product["id"] = product["_id"]
#         del product["_id"]

#         return product
    
#     @staticmethod
#     async def get_products():
#         products = []
#         async for product in product_collection.find({"status": True}):
#             product["id"] = product["_id"]
#             del product["_id"]
#             products.append(product)
#         return products
    
#     @staticmethod
#     async def update_product(product_id: str, data: dict, user_id: str):

#         existing = await product_collection.find_one({"_id": product_id, "status": True})

#         if not existing:
#             raise HTTPException(status_code=404, detail="Product not found")

#         data["updated_by"] = user_id

#         await product_collection.update_one(
#             {"_id": product_id},
#             {"$set": data}
#         )

#         return {"message": "Product updated successfully"}
    
#     @staticmethod
#     async def delete_product(product_id: str):

#         result = await product_collection.update_one(
#             {"_id": product_id},
#             {"$set": {"status": False}}
#         )

#         if result.modified_count == 0:
#             raise HTTPException(status_code=404, detail="Product not found")

#         return {"message": "Product deleted successfully"}
    
#     @staticmethod
#     async def add_product_image(product_id: str, image_url: str):

#         image = {
#             "_id": str(uuid.uuid4()),
#             "product_id": product_id,
#             "image_url": image_url,
#             "uploaded_at": datetime.utcnow()
#         }

#         await image_collection.insert_one(image)
#         return image
    
#     @staticmethod
#     async def get_product_images(product_id: str):
#         images = []

#         async for img in image_collection.find({"product_id": product_id}):
#             img["id"] = img["_id"]
#             del img["_id"]
#             images.append(img)

#         return images






# from fastapi import HTTPException
# from datetime import datetime
# import uuid
# from app.db.database import product_collection, image_collection
# from app.modules.product_catalog.utils import generate_sku


# class ProductService:

#     @staticmethod
#     async def create_product(data: dict, user_id: str):

#         # ✅ Validation
#         if data["selling_price"] < data["cost_price"]:
#             raise HTTPException(
#                 status_code=400,
#                 detail="Selling price cannot be less than cost price"
#             )

#         # ✅ Sequence logic for SKU
#         count = await product_collection.count_documents({
#             "name": data["name"],
#             "category_id": data["category_id"],
#             "brand": data.get("brand"),
#             "color": data.get("color")
#         })

#         sequence = count + 1

#         # ✅ Generate SKU
#         sku = generate_sku(
#             data["name"],
#             data["category_id"],
#             data.get("brand"),
#             data.get("color"),
#         )

#         # ✅ Ensure SKU uniqueness
#         existing_sku = await product_collection.find_one({"sku": sku})
#         if existing_sku:
#             raise HTTPException(status_code=400, detail="SKU already exists")

#         # ✅ Create product
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

#             # 🔥 Variant fields
#             "color": data.get("color"),
#             "size": data.get("size"),

#             "sku": sku,
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
#         async for product in product_collection.find({"status": True}):
#             product["id"] = product["_id"]
#             del product["_id"]
#             products.append(product)
#         return products

#     @staticmethod
#     async def update_product(product_id: str, data: dict, user_id: str):

#         existing = await product_collection.find_one({
#             "_id": product_id,
#             "status": True
#         })

#         if not existing:
#             raise HTTPException(status_code=404, detail="Product not found")

#         # 🔥 Regenerate SKU if important fields change
#         if any(k in data for k in ["name", "category_id", "brand", "color"]):
#             count = await product_collection.count_documents({
#                 "name": data.get("name", existing["name"]),
#                 "category_id": data.get("category_id", existing["category_id"]),
#                 "brand": data.get("brand", existing.get("brand")),
#                 "color": data.get("color", existing.get("color"))
#             })

#             sequence = count + 1

#             data["sku"] = generate_sku(
#                 data.get("name", existing["name"]),
#                 data.get("category_id", existing["category_id"]),
#                 data.get("brand", existing.get("brand")),
#                 data.get("color", existing.get("color")),
#                 sequence
#             )

#         data["updated_by"] = user_id
#         data["updated_at"] = datetime.utcnow()

#         await product_collection.update_one(
#             {"_id": product_id},
#             {"$set": data}
#         )

#         return {"message": "Product updated successfully"}

#     @staticmethod
#     async def delete_product(product_id: str):

#         result = await product_collection.update_one(
#             {"_id": product_id},
#             {"$set": {"status": False}}
#         )

#         if result.modified_count == 0:
#             raise HTTPException(status_code=404, detail="Product not found")

#         return {"message": "Product deleted successfully"}

#     @staticmethod
#     async def add_product_image(product_id: str, image_url: str):

#         image = {
#             "_id": str(uuid.uuid4()),
#             "product_id": product_id,
#             "image_url": image_url,
#             "uploaded_at": datetime.utcnow()
#         }

#         await image_collection.insert_one(image)
#         return image

#     @staticmethod
#     async def get_product_images(product_id: str):
#         images = []

#         async for img in image_collection.find({"product_id": product_id}):
#             img["id"] = img["_id"]
#             del img["_id"]
#             images.append(img)

#         return images

