
from datetime import datetime
from fastapi import HTTPException, status
from bson import ObjectId
from app.core.database import db
from app.services.invoice_service import generate_invoice_pdf, generate_amazon_style_email
from app.services.email_service import send_email_with_pdf
from app.services.notification_service import NotificationService
from app.utils.notification_helper import notify_user, notify_admin
from app.services.inventory_service import InventoryService
from app.services.audit_service import AuditService
from app.kafka.producer import send_event
from uuid import uuid4
from app.services.email_event_service import EmailEventService



class OrderService:
    def __init__(self, repo):
        self.repo = repo

    # ================= CREATE ORDER =================
    async def create_order(self, data, user):
        payload = data.dict()

        products = db["products"]

        final_items = []
        total = 0

        # ✅ LOOP PRODUCTS
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

        # ✅ NO WAREHOUSE HERE
        order_data = {
            "customer_name": payload["customer_name"],
            "phone": payload.get("phone"),
            "address": payload.get("address"),
            "email": payload.get("email"),
            "items": final_items,
            "user_id": str(user["_id"]),
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

    # ================= GET ORDERS =================
    async def get_orders(self):
        data = await self.repo.get_all()

        for o in data:
            o["id"] = str(o["_id"])
            del o["_id"]

        return data

#    ================= UPDATE STATUS =================
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

        # ================= CONFIRM ORDER =================
        if new_status == "confirmed":

            if current_status != "draft":
                raise HTTPException(400, "Only draft orders can be confirmed")

            updated_items = []

            for item in order["items"]:
                required_qty = item["quantity"]
                
                cursor = inventory.find({
                    "product_id":item["product_id"],
                    "stock":{"$gt":0}
                }).sort("stock",-1)
                
                allocations =[]
                total_allocated = 0
                
                async for stock in cursor:
                    available = stock["stock"]
                    
                    if available<=0:
                        continue
                    
                    take_qty = min(required_qty - total_allocated, available)
                    
                    allocations.append({
                        "warehouse_id": stock["warehouse_id"],
                        "warehouse_name":stock["warehouse_name"],
                        "quantity": take_qty
                    })
                    
                    total_allocated += take_qty
                    
                    if total_allocated >= required_qty:
                        break
                    
             #  Not enough total stock
            if total_allocated < required_qty:
                raise HTTPException(
                  400,
                  f"Insufficent total stock for {item["product_name"]}"
                )
            
            # ✅ attach allocations
            
            item["allocations"] = allocations
            updated_items.append(item)
            
                      

            # 🔽 DEDUCT STOCK
            for item in updated_items:
                for alloc in item["allocations"]:
                    await inventory.update_one(
                        {
                           "product_id": item["product_id"],
                           "warehouse_id": alloc["warehouse_id"]
                        },
                        {
                           "$inc": {"stock": -alloc["quantity"]}
                        }
                    )

                    # await InventoryService.check_low_stock(
                    #       item["product_id"],
                    #       alloc["warehouse_id"]
                    # )

            # 🔁 LOG MOVEMENT
            for item in updated_items:
                for alloc in item["allocations"]:
                    await logs.insert_one({
                        "product_id": item["product_id"],
                        "product_name": item["product_name"],
                        "warehouse_id": alloc["warehouse_id"],
                        "warehouse_name": alloc["warehouse_name"],
                        "movement_type": "order_out",
                        "quantity": item["quantity"],
                        "timestamp": datetime.utcnow(),
                        "remarks": f"Reserved for Order {order_id}"
                    })
                    
        # ================= WAREHOUSE SUMMARY =================

            warehouse_names = list(set([
                alloc["warehouse_name"]
                for item in updated_items
                for alloc in item["allocations"]
           ]))

            await self.repo.update(order_id, {
                "items": updated_items,
                "warehouse_name": ", ".join(warehouse_names)
            })

            order = await self.repo.get_by_id(order_id)

            pdf_bytes = generate_invoice_pdf(order, order_id)
            html_content = generate_amazon_style_email(order, order_id)

            # await send_email_with_pdf(
            #     order.get("email"),
            #     "🧾 Your Order Invoice",
            #     html_content,
            #     pdf_bytes
            # )

        # ================= CANCEL ORDER =================
        elif new_status == "cancelled":

            if current_status == "cancelled":
                raise HTTPException(400, "Order already cancelled")

            if current_status in ["confirmed", "packed"]:

                for item in order["items"]:
                    await inventory.update_one(
                        {
                            "product_id": item["product_id"],
                            "warehouse_id": item["warehouse_id"]
                        },
                        {
                            "$inc": {"stock": item["quantity"]}
                        }
                    )

                for item in order["items"]:
                    await logs.insert_one({
                        "product_id": item["product_id"],
                        "product_name": item["product_name"],
                        "warehouse_id": item["warehouse_id"],
                        "warehouse_name": item["warehouse_name"],
                        "movement_type": "order_cancel",
                        "quantity": item["quantity"],
                        "timestamp": datetime.utcnow(),
                        "remarks": f"Stock restored from cancelled Order {order_id}"
                    })

        # ================= RETURN ORDER =================
        elif new_status == "returned":

            if current_status != "delivered":
                raise HTTPException(400, "Only delivered orders can be returned")

            for item in order["items"]:
                await inventory.update_one(
                    {
                        "product_id": item["product_id"],
                        "warehouse_id": item["warehouse_id"]
                    },
                    {
                        "$inc": {"stock": item["quantity"]}
                    }
                )

            for item in order["items"]:
                await logs.insert_one({
                    "product_id": item["product_id"],
                    "product_name": item["product_name"],
                    "warehouse_id": item["warehouse_id"],
                    "warehouse_name": item["warehouse_name"],
                    "movement_type": "order_return",
                    "quantity": item["quantity"],
                    "timestamp": datetime.utcnow(),
                    "remarks": f"Returned Order {order_id}"
                })

        # ================= STATUS MESSAGES =================

        product_names = [item["product_name"] for item in order["items"]]

        
        product_text = ", ".join([
             f"{item['product_name']} (x{item['quantity']})"
             for item in order["items"][:2]
         ])

        if len(product_names) > 2:
           product_text += "..." 

        if new_status == "confirmed":
            title = "Order Confirmed"
            message = f"{product_text} confirmed (Order #{order_id})"

        elif new_status == "packed":
            title = "Order Packed"
            message = f"{product_text} packed (Order #{order_id})"

        elif new_status == "shipped":
            title = "Order Shipped"
            message = f"{product_text} shipped (Order #{order_id})"

        elif new_status == "delivered":
            title = "Order Delivered"
            message = f"{product_text} delivered (Order #{order_id})"

        elif new_status == "cancelled":
            title = "Order Cancelled"
            message = f"{product_text} cancelled (Order #{order_id})"

        elif new_status == "returned":
            title = "Order Returned"
            message = f"{product_text} returned (Order #{order_id})"

        else:
            title = "Order Update"
            message = f"{product_text} updated to {new_status} (Order #{order_id})"

        if new_status == "confirmed":
            notif_type = "order_confirmed"
        elif new_status == "cancelled":
            notif_type = "order_cancelled"
        else:
            notif_type = "order_update"
            

        # ✅ NOTIFICATIONS
        # await notify_admin(title, message,notif_type)

        # await notify_user(
        #     order["user_id"],
        #     title,
        #     message,
        #     notif_type
        # )
        
        #✅ SEND STATUS EMAIL TO USER (MINIMAL ADD)
        # if order.get("email"):

        #     subject_map = {
        #        "confirmed": "🧾 Order Confirmed",
        #        "packed": "📦 Order Packed",
        #       "shipped": "🚚 Order Shipped",
        #       "delivered": "✅ Order Delivered",
        #       "cancelled": "❌ Order Cancelled",
        #       "returned": "🔄 Order Returned"
        #    }

        #     subject = subject_map.get(new_status, "Order Update")

        #     html_content = generate_amazon_style_email(order, order_id)

            # try:
            #    await send_email_with_pdf(
            #       order.get("email"),
            #       subject,
            #       html_content #   )
            
            #     send_event("email_notifications", {
            #         "to": order.get("email"),
            #         "subject": subject,
            #         "html": html_content,
            #         "type": f"ORDER_{new_status.upper()}",
            #         "order_id": order_id,
            #         "status": new_status})
           
            # except Exception as e:
            #    print("Status email failed:", e)

        # ✅ FINAL STATUS UPDATE
        await self.repo.update(order_id, {
            "status": new_status,
            "updated_at": datetime.utcnow()
        })
        
        
        
        # old_status = order.get("status")
        
        # await AuditService.log(
        #     user_id=order["user_id"],
        #     action=f"ORDER_{new_status.upper()}",
        #     entity_type="order",
        #     entity_id=order_id,
        #     value={
        #            "items": [
        #                {
        #                     "product_name": item["product_name"],
        #                     "product_id": item["product_id"],
        #                     "warehouse_name": alloc["warehouse_name"],
        #                     "quantity": item["quantity"]
        #                 }
        #                 for item in order["items"]
        #             ],
        #             "status": new_status
        #            }
        #         )
        
        event = {
             "event_id": str(uuid4()),
             "type": f"ORDER_{new_status.upper()}",
             "order_id": order_id,
             "user_id": order["user_id"],
             "email": order.get("email"),
             "status": new_status,
             "items": order["items"],
             "customer": order.get("customer_name"),
             "total": order.get("total_amount"),
             "timestamp": datetime.utcnow().isoformat()
             }
        
        await EmailEventService.create({
             "event_id": event["event_id"],
             "order_id": order_id,
             "type": event["type"],
             "to": order.get("email"),
             "status": "PENDING",
             "retry_count": 0,
             "error": None
        })

        send_event("order_events", event)

        return {"message": f"Order {new_status} successfully"}
    
       

    