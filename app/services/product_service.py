from app.repositories.product_repo import ProductRepository
from app.repositories.category_repo import CategoryRepository
from app.models.product_model import ProductModel
from fastapi import HTTPException
from datetime import datetime
from typing import Optional, List

class ProductService:

    @staticmethod
    async def check_product_permission(product_id: str, user: dict):
        """Check if user has permission to modify this product"""
        
        # Admin can do anything
        if user["role"] == "admin":
            return True
        
        # Supplier can only modify their own products
        if user["role"] == "supplier":
            product = await ProductRepository.get_by_id(product_id)
            
            if not product:
                raise HTTPException(status_code=404, detail="Product not found")
            
            if product.get("created_by") != user["user_id"]:
                raise HTTPException(
                    status_code=403, 
                    detail="You can only modify products you created"
                )
            
            return True
        
        # Users cannot modify
        raise HTTPException(status_code=403, detail="Access denied")

    @staticmethod
    async def create_product(data: dict, image_url: str, image_metadata: dict, user_id: str):
        if not data.get("sku"):
            category_name = ""
            if data.get("category_id"):
                category = await CategoryRepository.get_by_id(data["category_id"])
                if category:
                    category_name = category["name"]
            data["sku"] = ProductModel.generate_sku(category_name)

        if await ProductRepository.check_sku_exists(data["sku"]):
            raise HTTPException(status_code=400, detail="SKU already exists")

        if data.get("category_id"):
            category = await CategoryRepository.get_by_id(data["category_id"])
            if not category:
                raise HTTPException(status_code=400, detail="Category not found")

        data["image_name"] = image_metadata.get("filename", "")
        data["image_size"] = image_metadata.get("size", 0)
        data["image_type"] = image_metadata.get("content_type", "")

        product = ProductModel.create(data, image_url, user_id)
        product_id = await ProductRepository.create(product)

        return {
            "message": "Product created successfully",
            "id": product_id,
            "sku": data["sku"]
        }

    @staticmethod
    async def get_all_products(page: int = 1, limit: int = 50):
        skip = (page - 1) * limit
        result = await ProductRepository.get_all(skip, limit)
        
        return {
            "total": result["total"],
            "page": page,
            "limit": limit,
            "products": result["products"]
        }

    @staticmethod
    async def get_product(product_id: str):
        product = await ProductRepository.get_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return product

    @staticmethod
    async def get_product_by_sku(sku: str):
        product = await ProductRepository.get_by_sku(sku)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return product

    @staticmethod
    async def get_products_by_creator(user_id: str, page: int = 1, limit: int = 50):
        """Get products created by specific user"""
        skip = (page - 1) * limit
        result = await ProductRepository.get_by_creator(user_id, skip, limit)
        
        return {
            "total": result["total"],
            "page": page,
            "limit": limit,
            "products": result["products"]
        }

    @staticmethod
    async def search_products(
        search: Optional[str] = None,
        category_id: Optional[str] = None,
        subcategory_id: Optional[str] = None,
        brand: Optional[str] = None,
        supplier_id: Optional[str] = None,
        status: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        in_stock: Optional[bool] = None,
        low_stock: Optional[bool] = None,
        tags: Optional[List[str]] = None,
        page: int = 1,
        limit: int = 50
    ):
        filters = {
            "search": search,
            "category_id": category_id,
            "subcategory_id": subcategory_id,
            "brand": brand,
            "supplier_id": supplier_id,
            "status": status,
            "min_price": min_price,
            "max_price": max_price,
            "in_stock": in_stock,
            "low_stock": low_stock,
            "tags": tags
        }

        skip = (page - 1) * limit
        result = await ProductRepository.search(filters, skip, limit)

        return {
            "total": result["total"],
            "page": page,
            "limit": limit,
            "products": result["products"]
        }

    @staticmethod
    async def get_products_by_category(category_id: str, page: int = 1, limit: int = 50):
        skip = (page - 1) * limit
        result = await ProductRepository.get_by_category(category_id, skip, limit)
        
        return {
            "total": result["total"],
            "page": page,
            "limit": limit,
            "products": result["products"]
        }

    @staticmethod
    async def get_low_stock_products():
        products = await ProductRepository.get_low_stock()
        return {
            "total": len(products),
            "products": products
        }

    @staticmethod
    async def update_product(product_id: str, data: dict, user_id: str):
        product = await ProductRepository.get_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        if data.get("sku") and data["sku"] != product["sku"]:
            if await ProductRepository.check_sku_exists(data["sku"], product_id):
                raise HTTPException(status_code=400, detail="SKU already exists")

        if data.get("category_id"):
            category = await CategoryRepository.get_by_id(data["category_id"])
            if not category:
                raise HTTPException(status_code=400, detail="Category not found")

        update_data = {k: v for k, v in data.items() if v is not None}
        update_data["updated_by"] = user_id

        await ProductRepository.update(product_id, update_data)
        return {"message": "Product updated successfully"}
    
    
    @staticmethod
    async def update_product_image(product_id: str, image_url: str, image_metadata: dict, user_id: str):
        product = await ProductRepository.get_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        update_data = {
            "image_url": image_url,
            "image_metadata": {
                "original_name": image_metadata.get("filename", ""),
                "size": image_metadata.get("size", 0),
                "mime_type": image_metadata.get("content_type", ""),
                "uploaded_at": datetime.utcnow()
            },
            "updated_by": user_id
        }

        await ProductRepository.update(product_id, update_data)
        return {"message": "Product image updated successfully"}

    @staticmethod
    async def update_quantity(product_id: str, quantity_change: int, user_id: str):
        product = await ProductRepository.get_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        new_quantity = product["quantity"] + quantity_change
        if new_quantity < 0:
            raise HTTPException(status_code=400, detail="Insufficient quantity")

        await ProductRepository.update_quantity(product_id, quantity_change)
        
        if new_quantity == 0:
            await ProductRepository.update(product_id, {
                "status": "out_of_stock",
                "updated_by": user_id
            })

        return {
            "message": "Quantity updated successfully",
            "new_quantity": new_quantity
        }

    @staticmethod
    async def delete_product(product_id: str):
        product = await ProductRepository.get_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        await ProductRepository.delete(product_id)
        return {"message": "Product deleted successfully"}
    
    # Add to existing ProductService class

    @staticmethod
    async def add_variant(product_id: str, variant_data: dict, user_id: str):
        product = await ProductRepository.get_by_id(product_id)
        if not product:
           raise HTTPException(status_code=404, detail="Product not found")
    
        variant = ProductModel.create_variant(variant_data, product["sku"])
        await ProductRepository.add_variant(product_id, variant)
    
        return {"message": "Variant added", "sku": variant["sku"]}

    @staticmethod
    async def update_variant(product_id: str, variant_sku: str, data: dict, user_id: str):
        product = await ProductRepository.get_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
    
        variant = next((v for v in product.get("variants", []) if v["sku"] == variant_sku), None)
        if not variant:
           raise HTTPException(status_code=404, detail="Variant not found")
    
        updated_variant = {**variant, **{k: v for k, v in data.items() if v is not None}}
        await ProductRepository.update_variant(product_id, variant_sku, updated_variant)
    
        return {"message": "Variant updated"}

    @staticmethod
    async def delete_variant(product_id: str, variant_sku: str, user_id: str):
        await ProductRepository.delete_variant(product_id, variant_sku)
        return {"message": "Variant deleted"}

    @staticmethod
    async def update_variant_quantity(product_id: str, variant_sku: str, change: int, user_id: str):
       product = await ProductRepository.get_by_id(product_id)
       if not product:
           raise HTTPException(status_code=404, detail="Product not found")
    
       variant = next((v for v in product.get("variants", []) if v["sku"] == variant_sku), None)
       if not variant:
            raise HTTPException(status_code=404, detail="Variant not found")
    
       new_qty = variant["quantity"] + change
       if new_qty < 0:
            raise HTTPException(status_code=400, detail="Insufficient quantity")
    
       await ProductRepository.update_variant_quantity(product_id, variant_sku, change)
       return {"message": "Quantity updated", "new_quantity": new_qty}