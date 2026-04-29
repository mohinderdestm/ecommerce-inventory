from fastapi import HTTPException
from datetime import datetime
from app.core.database import db
from bson import ObjectId
from app.services.notification_service import NotificationService
from app.services.email_service import send_email_with_pdf


LOW_STOCK_LIMIT = 2
ADMIN_EMAIL = "gagank1019@gmail.com" 


class InventoryService:
    def __init__(self, repo):
        self.repo = repo

    async def move_stock(self, data, user):
        payload = data.dict()

        movements = db["inventory_logs"]
        products = db["products"]
        warehouses = db["warehouses"]

        product_id = payload["product_id"]
        qty = payload["quantity"]
        movement_type = payload["movement_type"]

        # ✅ product name
        product = await products.find_one({"_id": ObjectId(product_id)})
        product_name = product.get("name") if product else None

        # ================= INWARD =================
        if movement_type == "inward":
            warehouse_id = payload["warehouse_id"]

            warehouse = await warehouses.find_one({"_id": ObjectId(warehouse_id)})
            warehouse_name = warehouse.get("name") if warehouse else None

            # ✅ FIX: update stock
            await self.repo.update_stock(product_id, warehouse_id, qty)

            await InventoryService.check_low_stock(product_id, warehouse_id)

            await InventoryService.check_low_stock(product_id, warehouse_id)

            await movements.insert_one({
                "product_id": product_id,
                "product_name": product_name,
                "warehouse_id": warehouse_id,
                "warehouse_name": warehouse_name,
                "movement_type": "inward",
                "quantity": qty,
                "performed_by": str(user["_id"]),
                "timestamp": datetime.utcnow(),
                "remarks": "Stock added"
            })

        # ================= OUTWARD =================
        elif movement_type == "outward":
            warehouse_id = payload["warehouse_id"]

            warehouse = await warehouses.find_one({"_id": ObjectId(warehouse_id)})
            warehouse_name = warehouse.get("name") if warehouse else None

            # ✅ FIX: get existing stock
            existing = await self.repo.get_inventory(product_id, warehouse_id)

            if not existing or existing.get("stock", 0) < qty:
                raise HTTPException(400, "Insufficient stock")

            await self.repo.update_stock(product_id, warehouse_id, -qty)
            await InventoryService.check_low_stock(product_id, warehouse_id)
            await InventoryService.check_low_stock(product_id, warehouse_id)

            await movements.insert_one({
                "product_id": product_id,
                "product_name": product_name,
                "warehouse_id": warehouse_id,
                "warehouse_name": warehouse_name,
                "movement_type": "outward",
                "quantity": qty,
                "performed_by": str(user["_id"]),
                "timestamp": datetime.utcnow(),
                "remarks": "Stock removed"
            })

        # ================= TRANSFER =================
        elif movement_type == "transfer":
            from_wh = payload["from_warehouse_id"]
            to_wh = payload["to_warehouse_id"]

            if from_wh == to_wh:
                raise HTTPException(400, "Same warehouse not allowed")

            # warehouse names
            from_wh_data = await warehouses.find_one({"_id": ObjectId(from_wh)})
            to_wh_data = await warehouses.find_one({"_id": ObjectId(to_wh)})

            from_name = from_wh_data.get("name") if from_wh_data else None
            to_name = to_wh_data.get("name") if to_wh_data else None

            # check stock
            existing = await self.repo.get_inventory(product_id, from_wh)

            if not existing or existing.get("stock", 0) < qty:
                raise HTTPException(400, "Insufficient stock")

            # deduct from source
            await self.repo.update_stock(product_id, from_wh, -qty)
            await InventoryService.check_low_stock(product_id, from_wh)
            await InventoryService.check_low_stock(product_id, from_wh)

            # add to destination
            await self.repo.update_stock(product_id, to_wh, qty)
            await InventoryService.check_low_stock(product_id, to_wh)
            
            await InventoryService.check_low_stock(product_id, to_wh)
            

            #  OUT log
            await movements.insert_one({
                "product_id": product_id,
                "product_name": product_name,
                "warehouse_id": from_wh,
                "warehouse_name": from_name,
                "movement_type": "transfer_out",
                "quantity": qty,
                "performed_by": str(user["_id"]),
                "timestamp": datetime.utcnow(),
                "remarks": f"Transferred to {to_name}"
            })

            #  IN log
            await movements.insert_one({
                "product_id": product_id,
                "product_name": product_name,
                "warehouse_id": to_wh,
                "warehouse_name": to_name,
                "movement_type": "transfer",
                "quantity": qty,
                "performed_by": str(user["_id"]),
                "timestamp": datetime.utcnow(),
                "remarks": f"Received from {from_name}"
            })

        else:
            raise HTTPException(400, "Invalid movement type")

        return {"message": "Stock updated successfully"}

    @staticmethod
    async def check_low_stock(product_id, warehouse_id):
        inventory = db["inventory"]
        products = db["products"]
        warehouses = db["warehouses"]

        stock = await inventory.find_one({
            "product_id": str(product_id),
            "warehouse_id": str(warehouse_id)
        })
        
        print("🔥 CHECKING STOCK FOR:", product_id, warehouse_id)
        print("📦 STOCK FOUND:", stock)

        if not stock:
            print("❌ Stock not found")
            return

        if stock.get("stock", 0) <= LOW_STOCK_LIMIT:
            
             # ✅ fetch names properly
            product = await products.find_one({"_id": ObjectId(product_id)})
            warehouse = await warehouses.find_one({"_id": ObjectId(warehouse_id)})

            product_name = product.get("name") if product else "Unknown Product"
            warehouse_name = warehouse.get("name") if warehouse else "Unknown Warehouse"
            

            # ❌ prevent duplicate alerts
            existing = await db["notifications"].find_one({
                "type": "low_stock",
                "product_id": product_id,
                "warehouse_id": warehouse_id,
                "is_read": False,
                "stock": stock["stock"]
            })

            if existing:
                print("⚠️ Low stock already notified (but sending email again)")
               

            await NotificationService.create({
                "role": "admin",
                "type": "low_stock",
                "title": "⚠️ Low Stock Alert",
                "message": f"{stock['product_name']} is low in {warehouse_name}. Remaining: {stock['stock']}",
                "product_id": product_id,
                "warehouse_id": warehouse_id,
                "created_at": datetime.utcnow()
            })
            
            
            html_content = f"""
            <div style="font-family:Arial; max-width:600px; margin:auto;">
                <h2 style="color:red;">⚠️ Low Stock Alert</h2>
                <p><b>Product:</b> {product_name}</p>
                <p><b>Warehouse:</b> {warehouse_name}</p>
                <p><b>Remaining:</b> {stock}</p>
            </div>
             """
            print("📧 EMAIL FUNCTION CALLED")
           

            try:
                 await send_email_with_pdf(
                   ADMIN_EMAIL,
                   f"⚠️ Low Stock: {stock['product_name']}",
                   html_content
                 )
            except Exception as e:
                 print("Low stock email failed:", e)


