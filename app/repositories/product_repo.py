from app.core.database import db
from bson import ObjectId
from datetime import datetime

class ProductRepository:

    @staticmethod
    def serialize(product) -> dict:
     if product is None:
        return None
    
     cost = product.get("cost_price", 0)
     selling = product.get("selling_price", 0)
     profit_margin = ((selling - cost) / cost * 100) if cost > 0 else 0
    
     return {
        "id": str(product["_id"]),
        "name": product.get("name", ""),
        "sku": product.get("sku", ""),
        "description": product.get("description", ""),
        "category_id": str(product["category_id"]) if product.get("category_id") else None,
        "subcategory_id": str(product["subcategory_id"]) if product.get("subcategory_id") else None,
        "brand": product.get("brand", ""),
        "supplier_id": product.get("supplier_id"),  # NEW
        "cost_price": product.get("cost_price", 0),
        "selling_price": product.get("selling_price", 0),
        "quantity": product.get("quantity", 0),
        "reorder_level": product.get("reorder_level", 10),
        "tax_percentage": product.get("tax_percentage", 0),
        "unit": product.get("unit", "pcs"),
        "status": product.get("status", "active"),
        "image_url": product.get("image_url", ""),
        "variants": product.get("variants", []),  # NEW
        "tags": product.get("tags", []),
        "profit_margin": round(profit_margin, 2),
        "created_by": str(product.get("created_by", "")),
        "updated_by": str(product.get("updated_by", "")),
        "created_at": product.get("created_at"),
        "updated_at": product.get("updated_at")
     }
   
    @staticmethod
    async def create(product: dict):
        result = await db["products"].insert_one(product)
        return str(result.inserted_id)

    @staticmethod
    async def get_all(skip: int = 0, limit: int = 50):
        products = []
        cursor = db["products"].find().skip(skip).limit(limit).sort("created_at", -1)
        
        async for p in cursor:
            products.append(ProductRepository.serialize(p))
        
        total = await db["products"].count_documents({})
        return {"products": products, "total": total}

    @staticmethod
    async def get_by_id(product_id: str):
        if not ObjectId.is_valid(product_id):
            return None
        
        product = await db["products"].find_one({"_id": ObjectId(product_id)})
        return ProductRepository.serialize(product)

    @staticmethod
    async def get_by_sku(sku: str):
        product = await db["products"].find_one({"sku": sku})
        return ProductRepository.serialize(product)

    # Get products by creator
    @staticmethod
    async def get_by_creator(user_id: str, skip: int = 0, limit: int = 50):
        products = []
        query = {"created_by": user_id}
        cursor = db["products"].find(query).skip(skip).limit(limit).sort("created_at", -1)
        
        async for p in cursor:
            products.append(ProductRepository.serialize(p))
        
        total = await db["products"].count_documents(query)
        return {"products": products, "total": total}

    @staticmethod
    async def get_by_category(category_id: str, skip: int = 0, limit: int = 50):
        products = []
        query = {"category_id": ObjectId(category_id), "status": "active"}
        cursor = db["products"].find(query).skip(skip).limit(limit)
        
        async for p in cursor:
            products.append(ProductRepository.serialize(p))
        
        total = await db["products"].count_documents(query)
        return {"products": products, "total": total}

    @staticmethod
    async def search(filters: dict, skip: int = 0, limit: int = 50):
        query = {}

        if filters.get("search"):
            search_text = filters["search"]
            query["$or"] = [
                {"name": {"$regex": search_text, "$options": "i"}},
                {"sku": {"$regex": search_text, "$options": "i"}},
                {"description": {"$regex": search_text, "$options": "i"}}
            ]

        if filters.get("category_id"):
            query["category_id"] = ObjectId(filters["category_id"])

        if filters.get("subcategory_id"):
            query["subcategory_id"] = ObjectId(filters["subcategory_id"])

        if filters.get("brand"):
            query["brand"] = {"$regex": filters["brand"], "$options": "i"}

        if filters.get("supplier_id"):
            query["supplier_ids"] = ObjectId(filters["supplier_id"])

        if filters.get("status"):
            query["status"] = filters["status"]

        if filters.get("min_price") is not None or filters.get("max_price") is not None:
            query["selling_price"] = {}
            if filters.get("min_price") is not None:
                query["selling_price"]["$gte"] = filters["min_price"]
            if filters.get("max_price") is not None:
                query["selling_price"]["$lte"] = filters["max_price"]

        if filters.get("in_stock") is True:
            query["quantity"] = {"$gt": 0}

        if filters.get("low_stock") is True:
            query["$expr"] = {"$lte": ["$quantity", "$reorder_level"]}

        if filters.get("tags"):
            query["tags"] = {"$in": filters["tags"]}

        products = []
        cursor = db["products"].find(query).skip(skip).limit(limit).sort("created_at", -1)
        
        async for p in cursor:
            products.append(ProductRepository.serialize(p))

        total = await db["products"].count_documents(query)
        
        return {"products": products, "total": total}

    @staticmethod
    async def get_low_stock():
        products = []
        pipeline = [
            {"$match": {"$expr": {"$lte": ["$quantity", "$reorder_level"]}}},
            {"$sort": {"quantity": 1}}
        ]
        
        async for p in db["products"].aggregate(pipeline):
            products.append(ProductRepository.serialize(p))
        
        return products

    @staticmethod
    async def update(product_id: str, data: dict):
        if not ObjectId.is_valid(product_id):
            return False
        
        data["updated_at"] = datetime.utcnow()
        
        result = await db["products"].update_one(
            {"_id": ObjectId(product_id)},
            {"$set": data}
        )
        return result.modified_count > 0
    
    # Add to existing ProductRepository class

    @staticmethod
    async def add_variant(product_id: str, variant: dict):
        if not ObjectId.is_valid(product_id):
            return False
        result = await db["products"].update_one(
            {"_id": ObjectId(product_id)},
            {
            "$push": {"variants": variant},
            "$set": {"updated_at": datetime.utcnow()}
           }
          )
        return result.modified_count > 0

    @staticmethod
    async def update_variant(product_id: str, variant_sku: str, data: dict):
        if not ObjectId.is_valid(product_id):
            return False
        result = await db["products"].update_one(
            {"_id": ObjectId(product_id), "variants.sku": variant_sku},
            {
             "$set": {
                "variants.$": {**data, "sku": variant_sku},
                "updated_at": datetime.utcnow()
            }
         }
         )
        return result.modified_count > 0

    @staticmethod
    async def delete_variant(product_id: str, variant_sku: str):
        if not ObjectId.is_valid(product_id):
           return False
        result = await db["products"].update_one(
           {"_id": ObjectId(product_id)},
           {
            "$pull": {"variants": {"sku": variant_sku}},
            "$set": {"updated_at": datetime.utcnow()}
           }
       )
        return result.modified_count > 0

    @staticmethod
    async def update_variant_quantity(product_id: str, variant_sku: str, change: int):
        if not ObjectId.is_valid(product_id):
           return False
        result = await db["products"].update_one(
            {"_id": ObjectId(product_id), "variants.sku": variant_sku},
            {
            "$inc": {"variants.$.quantity": change},
            "$set": {"updated_at": datetime.utcnow()}
           }
        )
        return result.modified_count > 0

    @staticmethod
    async def get_by_supplier(supplier_id: str, skip: int = 0, limit: int = 50):
      products = []
      query = {"supplier_id": supplier_id}
      async for p in db["products"].find(query).skip(skip).limit(limit):
         products.append(ProductRepository.serialize(p))
      total = await db["products"].count_documents(query)
      return {"products": products, "total": total}

    @staticmethod
    async def update_quantity(product_id: str, quantity_change: int):
        if not ObjectId.is_valid(product_id):
            return False
        
        result = await db["products"].update_one(
            {"_id": ObjectId(product_id)},
            {
                "$inc": {"quantity": quantity_change},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        return result.modified_count > 0

    @staticmethod
    async def delete(product_id: str):
        if not ObjectId.is_valid(product_id):
            return False
        
        result = await db["products"].delete_one({"_id": ObjectId(product_id)})
        return result.deleted_count > 0

    @staticmethod
    async def check_sku_exists(sku: str, exclude_id: str = None) -> bool:
        query = {"sku": sku}
        if exclude_id:
            query["_id"] = {"$ne": ObjectId(exclude_id)}
        
        product = await db["products"].find_one(query)
        return product is not None