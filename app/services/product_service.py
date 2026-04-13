from fastapi import HTTPException, status
from app.utils.sku_generator import generate_sku

from app.repositories.supplier_repository import SupplierRepository
from app.services.supplier_service import SupplierService
from app.core.database import db

class ProductService:

    def __init__(self, repo):
        self.repo = repo

    
    async def get_product(self, product_id):
        product = await self.repo.get_by_id(product_id)

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )

        product["_id"] = str(product["_id"])
        return product
    

    async def create_product(self, data, user):
        data = data.dict()
        data["status"] = "active"
        data["created_by"] = str(
        user.get("user_id") or 
        user.get("id") or 
        user.get("_id")
        )
        data["is_deleted"] = False

        base_name = data["name"]

        try:
            if data.get("variants"):
                for idx, v in enumerate(data["variants"]):

                    attributes = v.get("attributes", {})

                    if attributes:
                        attr_string = "-".join(
                             f"{k}:{v}" for k, v in sorted(attributes.items())
                        )
                        sku_input = f"{base_name}-{attr_string}"
                    else:
                        sku_input = f"{base_name}-{idx}"

                    v["sku"] = generate_sku(sku_input)

            else:
                data["sku"] = generate_sku(base_name)

        except Exception as e:
            print("SKU Error:", e)
            data["sku"] = base_name[:10]
            
        # ✅ HANDLE SUPPLIER LOGIC
        if user.get("role") == "supplier":
            supplier_repo = SupplierRepository(db)
            supplier_service = SupplierService(supplier_repo)

            supplier = await supplier_service.get_supplier_by_user(user)

            if not supplier:
                raise HTTPException(404, "Supplier not found")

            data["supplier_id"] = str(supplier["_id"])

        product_id = await self.repo.create(data)
        return {"_id": product_id}
      


    async def delete_product(self, product_id):
        await self.repo.soft_delete(product_id)
        return {"message": "Product deleted"}     
    
    async def update_product(self, product_id, data):
        update_data = data.dict(exclude_unset=True)

        if "status" in update_data:
           update_data["status"] = update_data["status"]

        result = await self.repo.update(product_id, data.dict(exclude_unset=True))

        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )

        return {"message": "Product updated"}


    