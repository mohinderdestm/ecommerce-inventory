from fastapi import HTTPException
from bson import ObjectId
from app.core.database import db
from app.services.audit_service import AuditService

class WarehouseService:
    def __init__(self, repo):
        self.repo = repo
        self.db = db

    async def create_warehouse(self, data,user):
        warehouse_data = data.dict()
        warehouse_data["manager_id"] = str(user["_id"])  

        warehouse_id = await self.repo.create(warehouse_data)
        
        await AuditService.log(
        user_id=str(user["_id"]),
        action="WAREHOUSE_CREATED",
        entity_type="warehouse",
        entity_id=str(warehouse_id),
        value={
            "name": warehouse_data.get("name"),
            "location": warehouse_data.get("location")
        }
      )
        
        return {"id": warehouse_id}

    
    async def list_warehouses(self):
       warehouses = await self.repo.get_all()
       result = []

       for w in warehouses:
            manager_name = None

            manager_id = w.get("manager_id")

            if manager_id and ObjectId.is_valid(manager_id):
               user = await self.db["users"].find_one(
                {"_id": ObjectId(manager_id)}
               )
               if user:
                   manager_name = user.get("name")

            staff_names = []
            for sid in w.get("staff_ids", []):
                if sid and ObjectId.is_valid(sid):
                    user = await self.db["users"].find_one(
                        {"_id": ObjectId(sid)}
                    )
                    if user:
                      staff_names.append(user.get("name"))

            result.append({
            "id": str(w["_id"]),
            "name": w.get("name"),
            "location": w.get("location"),
            "manager_name": manager_name,
            "staff_names": staff_names
        })

       return result

    async def update_warehouse(self, warehouse_id, payload,user):
        update_data = payload.dict(exclude_unset=True)

        result = await self.repo.update(warehouse_id, payload.dict(exclude_unset=True))

        if result.matched_count == 0:
            raise HTTPException(404, "Warehouse not found")
        
        await AuditService.log(
            user_id=str(user["_id"]),
            action="WAREHOUSE_UPDATED",
            entity_type="warehouse",
            entity_id=warehouse_id,
            value=update_data
        )

        return {"message": "Updated"}

    async def delete_warehouse(self, warehouse_id,user):
        
        warehouse = await self.repo.get_by_id(warehouse_id)
        await self.repo.delete(warehouse_id)
        
        await AuditService.log(
        user_id=str(user["_id"]),
        action="WAREHOUSE_DELETED",
        entity_type="warehouse",
        entity_id=warehouse_id,
        value={
            "name": warehouse.get("name"),
            "location": warehouse.get("location")
        }
      )
        
        return {"message": "Deleted"}
    
   

    async def get_warehouse_inventory(self, warehouse_id):
        inventory = db["inventory"]
        products = db["products"]

        cursor = inventory.find({"warehouse_id": warehouse_id})

        result = []

        async for item in cursor:
           product = await products.find_one({
              "_id": ObjectId(item["product_id"])
           })
           result.append({
              "product_name": item.get("product_name"),
               "category": product.get("category") if product else "N/A",
               "stock": item.get("stock", 0)
        })

        return result