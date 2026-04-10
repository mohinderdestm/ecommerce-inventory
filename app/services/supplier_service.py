from app.repositories.supplier_repo import SupplierRepository
from app.repositories.product_repo import ProductRepository
from app.models.supplier_model import SupplierModel
from fastapi import HTTPException

class SupplierService:

    @staticmethod
    async def create(data: dict, user_id: str):
        supplier = SupplierModel.create(data, user_id)
        supplier_id = await SupplierRepository.create(supplier)
        return {"message": "Supplier created", "id": supplier_id}

    @staticmethod
    async def get_all(page: int = 1, limit: int = 50, status: str = None):
        skip = (page - 1) * limit
        result = await SupplierRepository.get_all(skip, limit, status)
        return {"total": result["total"], "page": page, "suppliers": result["suppliers"]}

    @staticmethod
    async def get_by_id(supplier_id: str):
        supplier = await SupplierRepository.get_by_id(supplier_id)
        if not supplier:
            raise HTTPException(status_code=404, detail="Supplier not found")
        return supplier

    @staticmethod
    async def search(query: str, page: int = 1, limit: int = 50):
        skip = (page - 1) * limit
        result = await SupplierRepository.search(query, skip, limit)
        return {"total": result["total"], "page": page, "suppliers": result["suppliers"]}

    @staticmethod
    async def update(supplier_id: str, data: dict):
        supplier = await SupplierRepository.get_by_id(supplier_id)
        if not supplier:
            raise HTTPException(status_code=404, detail="Supplier not found")
        
        update_data = {k: v for k, v in data.items() if v is not None}
        await SupplierRepository.update(supplier_id, update_data)
        return {"message": "Supplier updated"}

    @staticmethod
    async def update_rating(supplier_id: str, rating: float):
        if rating < 0 or rating > 5:
            raise HTTPException(status_code=400, detail="Rating must be 0-5")
        await SupplierRepository.update_rating(supplier_id, rating)
        return {"message": "Rating updated"}

    @staticmethod
    async def delete(supplier_id: str):
        supplier = await SupplierRepository.get_by_id(supplier_id)
        if not supplier:
            raise HTTPException(status_code=404, detail="Supplier not found")
        await SupplierRepository.delete(supplier_id)
        return {"message": "Supplier deleted"}

    @staticmethod
    async def get_products(supplier_id: str, page: int = 1, limit: int = 50):
        skip = (page - 1) * limit
        result = await ProductRepository.get_by_supplier(supplier_id, skip, limit)
        return {"total": result["total"], "page": page, "products": result["products"]}

    @staticmethod
    async def get_performance(supplier_id: str):
        supplier = await SupplierRepository.get_by_id(supplier_id)
        if not supplier:
            raise HTTPException(status_code=404, detail="Supplier not found")

        products = await SupplierRepository.get_products(supplier_id)

        # Calculate product metrics
        total_products = len(products)
        active_products = sum(1 for p in products if p.get("status") == "active")
        low_stock_products = sum(1 for p in products if p.get("quantity", 0) > 0 and p.get("quantity", 0) <= p.get("reorder_level", 10))
        out_of_stock_products = sum(1 for p in products if p.get("quantity", 0) == 0 or p.get("status") == "out_of_stock")

        # Calculate inventory value
        total_inventory_value = sum(
            p.get("selling_price", 0) * p.get("quantity", 0)
            for p in products
        )

        return {
            "supplier": supplier["name"],
            "rating": supplier.get("rating", 0),
            "total_products": total_products,
            "active_products": active_products,
            "low_stock_products": low_stock_products,
            "out_of_stock_products": out_of_stock_products,
            "total_inventory_value": total_inventory_value,
            "total_orders": supplier.get("total_orders", 0),
            "total_amount": supplier.get("total_amount", 0),
            "avg_order_value": supplier.get("total_amount", 0) / supplier.get("total_orders", 1) if supplier.get("total_orders", 0) > 0 else 0,
            "products_count": total_products,
            "status": supplier.get("status", "active")
        }