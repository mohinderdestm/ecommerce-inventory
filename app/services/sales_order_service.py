from datetime import datetime
from fastapi import HTTPException, status
from bson import ObjectId
from app.core.database import db
from datetime import datetime


class OrderService:
    def __init__(self, repo):
        self.repo = repo

    async def create_order(self, data):
        payload = data.dict()

        products = db["products"]
        warehouses = db["warehouses"]

        # ✅ FIND WAREHOUSE BY NAME
        warehouse = await warehouses.find_one({
            "name": payload["warehouse_name"]
        })

        if not warehouse:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Warehouse not found"
            )

        warehouse_id = str(warehouse["_id"])

        final_items = []
        total = 0

        # ✅ LOOP PRODUCTS BY NAME
        for item in payload["items"]:
            product = await products.find_one({
                "name": item["product_name"]
            })

            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product '{item['product_name']}' not found"
                )

            product_id = str(product["_id"])

            if item["quantity"] <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Quantity must be greater than 0"
                )

            item_total = item["quantity"] * item["price"]
            total += item_total

            final_items.append({
                "product_id": product_id,
                "product_name": item["product_name"],
                "quantity": item["quantity"],
                "price": item["price"]
            })

        order_data = {
            "customer_name": payload["customer_name"],
            "warehouse_id": warehouse_id,
            "warehouse_name": payload["warehouse_name"],
            "items": final_items,
            "total_amount": total,
            "status": "draft",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        order_id = await self.repo.create(order_data)

        return {
            "id": order_id,
            "message": "Order created successfully"
        }

    async def get_orders(self):
        data = await self.repo.get_all()

        for o in data:
            o["id"] = str(o["_id"])
            del o["_id"]

        return data


    async def update_status(self, order_id, new_status):
        inventory = db["inventory"]
        logs = db["inventory_logs"]
        
        order = await self.repo.get_by_id(order_id)

        if not order:
            raise HTTPException(404, "Order not found")

        current_status = order.get("status")
        
        valid_transitions = {
            "draft": ["confirmed", "cancelled"],
            "confirmed": ["packed", "cancelled"],
            "packed": ["shipped", "cancelled"],
            "shipped": ["delivered"],
            "delivered": ["returned"],
            "cancelled": []
           }

        if new_status not in valid_transitions.get(current_status, []):
            raise HTTPException(
                 400,
                 f"Cannot change status from {current_status} to {new_status}"
            )

        # ✅ CONFIRM ORDER
        if new_status == "confirmed":

            if current_status != "draft":
                raise HTTPException(400, "Only draft orders can be confirmed")

            inventory = self.repo.collection.database["inventory"]

            # 🔍 CHECK STOCK
            for item in order["items"]:
                stock = await inventory.find_one({
                    "product_id": item["product_id"],
                    "warehouse_id": order["warehouse_id"]
                })

                if not stock or stock.get("stock", 0) < item["quantity"]:
                    raise HTTPException(
                        400,
                        f"Insufficient stock for {item['product_name']}"
                    )

            # 🔽 DEDUCT STOCK
            for item in order["items"]:
                await inventory.update_one(
                    {
                        "product_id": item["product_id"],
                        "warehouse_id": order["warehouse_id"]
                    },
                    {
                        "$inc": {"stock": -item["quantity"]}
                    }
                )

            # 🔁 LOG MOVEMENT
            movements = self.repo.collection.database["inventory_logs"]

            for item in order["items"]:
                await movements.insert_one({
                    "product_id": item["product_id"],
                    "product_name": item["product_name"],
                    "warehouse_id": order["warehouse_id"],
                    "warehouse_name": order["warehouse_name"],
                    "movement_type": "order_out",
                    "quantity": item["quantity"],
                    "timestamp": datetime.utcnow(),
                    "remarks": f"Reserved for Order {order_id}"
                })
        # ================= CANCEL ORDER =================
        elif new_status == "cancelled":

            if current_status == "cancelled":
                raise HTTPException(400, "Order already cancelled")

              # ✅ restore stock if already deducted
            if current_status in ["confirmed", "packed"]:

                for item in order["items"]:
                    await inventory.update_one(
                {
                    "product_id": item["product_id"],
                    "warehouse_id": order["warehouse_id"]
                },
                {
                    "$inc": {"stock": item["quantity"]}
                }
                )

                for item in order["items"]:
                    await logs.insert_one({
                        "product_id": item["product_id"],
                        "product_name": item["product_name"],
                        "warehouse_id": order["warehouse_id"],
                        "warehouse_name": order["warehouse_name"],
                        "movement_type": "order_cancel",
                        "quantity": item["quantity"],
                        "timestamp": datetime.utcnow(),
                        "remarks": f"Stock restored from cancelled Order {order_id}"
            })
                    
        # ================= OTHER STATUS (packed, shipped, delivered) =================
        elif new_status in ["packed", "shipped", "delivered"]:
            pass  # only status update, no stock change

        
        # ================= RETURN ORDER =================
        elif new_status == "returned":

            if current_status != "delivered":
               raise HTTPException(400, "Only delivered orders can be returned")

              # 🔁 RESTORE STOCK
            for item in order["items"]:
                await inventory.update_one(
            {
                "product_id": item["product_id"],
                "warehouse_id": order["warehouse_id"]
            },
            {
                "$inc": {"stock": item["quantity"]}
            }
        )

             # 🔁 LOG RETURN
            for item in order["items"]:
                await logs.insert_one({
                    "product_id": item["product_id"],
                    "product_name": item["product_name"],
                    "warehouse_id": order["warehouse_id"],
                    "warehouse_name": order["warehouse_name"],
                    "movement_type": "order_return",
                    "quantity": item["quantity"],
                    "timestamp": datetime.utcnow(),
                    "remarks": f"Returned Order {order_id}"
            })
                
         # ================= INVALID =================
        else:
           raise HTTPException(400, "Invalid status update")
        

        # ✅ UPDATE STATUS
        await self.repo.update(order_id, {
            "status": new_status,
            "updated_at": datetime.utcnow()
        })

        return {"message": f"Order {new_status} successfully"}