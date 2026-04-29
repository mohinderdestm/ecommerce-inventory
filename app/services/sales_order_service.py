# from datetime import datetime
# from fastapi import HTTPException, status
# from bson import ObjectId
# from app.core.database import db
# from datetime import datetime


# class OrderService:
#     def __init__(self, repo):
#         self.repo = repo

#     async def create_order(self, data):
#         payload = data.dict()

#         products = db["products"]
#         warehouses = db["warehouses"]

#         # ✅ FIND WAREHOUSE BY NAME
#         # warehouse = await warehouses.find_one({
#         #     "name": payload["warehouse_name"]
#         # })

#         # if not warehouse:
#         #     raise HTTPException(
#         #         status_code=status.HTTP_404_NOT_FOUND,
#         #         detail="Warehouse not found"
#         #     )

#         # warehouse_id = str(warehouse["_id"])

#         final_items = []
#         total = 0

#         # ✅ LOOP PRODUCTS BY NAME
#         for item in payload["items"]:
#             product = await products.find_one({
#                 "name": item["product_name"]
#             })

#             if not product:
#                 raise HTTPException(
#                     status_code=status.HTTP_404_NOT_FOUND,
#                     detail=f"Product '{item['product_name']}' not found"
#                 )

#             product_id = str(product["_id"])

#             if item["quantity"] <= 0:
#                 raise HTTPException(
#                     status_code=status.HTTP_400_BAD_REQUEST,
#                     detail="Quantity must be greater than 0"
#                 )

#             item_total = item["quantity"] * item["price"]
#             total += item_total

#             final_items.append({
#                 "product_id": product_id,
#                 "product_name": item["product_name"],
#                 "quantity": item["quantity"],
#                 "price": item["price"]
#             })

#         order_data = {
#             "customer_name": payload["customer_name"],
#             # "warehouse_id": warehouse_id,
#             # "warehouse_name": payload["warehouse_name"],
#             "items": final_items,
#             "total_amount": total,
#             "status": "draft",
#             "created_at": datetime.utcnow(),
#             "updated_at": datetime.utcnow()
#         }

#         order_id = await self.repo.create(order_data)

#         return {
#             "id": order_id,
#             "message": "Order created successfully"
#         }

#     async def get_orders(self):
#         data = await self.repo.get_all()

#         for o in data:
#             o["id"] = str(o["_id"])
#             del o["_id"]

#         return data


#     async def update_status(self, order_id, new_status):
#         inventory = db["inventory"]
#         logs = db["inventory_logs"]
        
#         order = await self.repo.get_by_id(order_id)

#         if not order:
#             raise HTTPException(404, "Order not found")

#         current_status = order.get("status")
        
#         valid_transitions = {
#             "draft": ["confirmed", "cancelled"],
#             "confirmed": ["packed", "cancelled"],
#             "packed": ["shipped", "cancelled"],
#             "shipped": ["delivered"],
#             "delivered": ["returned"],
#             "cancelled": []
#            }

#         if new_status not in valid_transitions.get(current_status, []):
#             raise HTTPException(
#                  400,
#                  f"Cannot change status from {current_status} to {new_status}"
#             )

#         # ✅ CONFIRM ORDER
#         if new_status == "confirmed":

#             if current_status != "draft":
#                 raise HTTPException(400, "Only draft orders can be confirmed")

#             inventory = self.repo.collection.database["inventory"]

#             # 🔍 CHECK STOCK
#             for item in order["items"]:
#                 stock = await inventory.find_one({
#                     "product_id": item["product_id"],
#                     "warehouse_id": order["warehouse_id"]
#                 })

#                 if not stock or stock.get("stock", 0) < item["quantity"]:
#                     raise HTTPException(
#                         400,
#                         f"Insufficient stock for {item['product_name']}"
#                     )

#             # 🔽 DEDUCT STOCK
#             for item in order["items"]:
#                 await inventory.update_one(
#                     {
#                         "product_id": item["product_id"],
#                         "warehouse_id": order["warehouse_id"]
#                     },
#                     {
#                         "$inc": {"stock": -item["quantity"]}
#                     }
#                 )

#             # 🔁 LOG MOVEMENT
#             movements = self.repo.collection.database["inventory_logs"]

#             for item in order["items"]:
#                 await movements.insert_one({
#                     "product_id": item["product_id"],
#                     "product_name": item["product_name"],
#                     "warehouse_id": order["warehouse_id"],
#                     "warehouse_name": order["warehouse_name"],
#                     "movement_type": "order_out",
#                     "quantity": item["quantity"],
#                     "timestamp": datetime.utcnow(),
#                     "remarks": f"Reserved for Order {order_id}"
#                 })
#         # ================= CANCEL ORDER =================
#         elif new_status == "cancelled":

#             if current_status == "cancelled":
#                 raise HTTPException(400, "Order already cancelled")

#               # ✅ restore stock if already deducted
#             if current_status in ["confirmed", "packed"]:

#                 for item in order["items"]:
#                     await inventory.update_one(
#                 {
#                     "product_id": item["product_id"],
#                     "warehouse_id": order["warehouse_id"]
#                 },
#                 {
#                     "$inc": {"stock": item["quantity"]}
#                 }
#                 )

#                 for item in order["items"]:
#                     await logs.insert_one({
#                         "product_id": item["product_id"],
#                         "product_name": item["product_name"],
#                         "warehouse_id": order["warehouse_id"],
#                         "warehouse_name": order["warehouse_name"],
#                         "movement_type": "order_cancel",
#                         "quantity": item["quantity"],
#                         "timestamp": datetime.utcnow(),
#                         "remarks": f"Stock restored from cancelled Order {order_id}"
#             })
                    
#         # ================= OTHER STATUS (packed, shipped, delivered) =================
#         elif new_status in ["packed", "shipped", "delivered"]:
#             pass  # only status update, no stock change

        
#         # ================= RETURN ORDER =================
#         elif new_status == "returned":

#             if current_status != "delivered":
#                raise HTTPException(400, "Only delivered orders can be returned")

#               # 🔁 RESTORE STOCK
#             for item in order["items"]:
#                 await inventory.update_one(
#             {
#                 "product_id": item["product_id"],
#                 "warehouse_id": order["warehouse_id"]
#             },
#             {
#                 "$inc": {"stock": item["quantity"]}
#             }
#         )

#              # 🔁 LOG RETURN
#             for item in order["items"]:
#                 await logs.insert_one({
#                     "product_id": item["product_id"],
#                     "product_name": item["product_name"],
#                     "warehouse_id": order["warehouse_id"],
#                     "warehouse_name": order["warehouse_name"],
#                     "movement_type": "order_return",
#                     "quantity": item["quantity"],
#                     "timestamp": datetime.utcnow(),
#                     "remarks": f"Returned Order {order_id}"
#             })
                
#          # ================= INVALID =================
#         else:
#            raise HTTPException(400, "Invalid status update")
        

#         # ✅ UPDATE STATUS
#         await self.repo.update(order_id, {
#             "status": new_status,
#             "updated_at": datetime.utcnow()
#         })

#         return {"message": f"Order {new_status} successfully"}


# from datetime import datetime
# from fastapi import HTTPException, status
# from bson import ObjectId
# from app.core.database import db
# from app.services.invoice_service import generate_invoice_pdf, generate_amazon_style_email
# from app.services.email_service import send_email_with_pdf
# from app.services.notification_service import NotificationService
# from app.utils.notification_helper import notify_user, notify_admin
# from app.services.inventory_service import InventoryService



# class OrderService:
#     def __init__(self, repo):
#         self.repo = repo

#     # ================= CREATE ORDER =================
#     async def create_order(self, data,user):
#         payload = data.dict()

#         products = db["products"]

#         final_items = []
#         total = 0

#         # ✅ LOOP PRODUCTS
#         for item in payload["items"]:
#             product = await products.find_one({
#                 "name": item["product_name"]
#             })

#             if not product:
#                 raise HTTPException(
#                     status_code=status.HTTP_404_NOT_FOUND,
#                     detail=f"Product '{item['product_name']}' not found"
#                 )

#             product_id = str(product["_id"])

#             if item["quantity"] <= 0:
#                 raise HTTPException(
#                     status_code=status.HTTP_400_BAD_REQUEST,
#                     detail="Quantity must be greater than 0"
#                 )

#             item_total = item["quantity"] * item["price"]
#             total += item_total

#             final_items.append({
#                 "product_id": product_id,
#                 "product_name": item["product_name"],
#                 "quantity": item["quantity"],
#                 "price": item["price"]
#             })

#         # ✅ NO WAREHOUSE HERE
#         order_data = {
#             "customer_name": payload["customer_name"],
#              "phone": payload.get("phone"),
#              "address": payload.get("address"),
#              "email": payload.get("email"),  
#              "items": final_items,
#              "user_id": str(user["_id"]), 
#              "total_amount": total,
#              "status": "draft",
#              "created_at": datetime.utcnow(),
#              "updated_at": datetime.utcnow()
#         }

#         order_id = await self.repo.create(order_data)

#         return {
#             "id": order_id,
#             "message": "Order created successfully"
#         }

#     # ================= GET ORDERS =================
#     async def get_orders(self):
#         data = await self.repo.get_all()

#         for o in data:
#             o["id"] = str(o["_id"])
#             del o["_id"]

#         return data

#     # ================= UPDATE STATUS =================
#     async def update_status(self, order_id, new_status):
#         inventory = db["inventory"]
#         logs = db["inventory_logs"]

#         order = await self.repo.get_by_id(order_id)

#         if not order:
#             raise HTTPException(404, "Order not found")

#         current_status = order.get("status")

#         valid_transitions = {
#             "draft": ["confirmed", "cancelled"],
#             "confirmed": ["packed", "cancelled"],
#             "packed": ["shipped", "cancelled"],
#             "shipped": ["delivered"],
#             "delivered": ["returned"],
#             "cancelled": []
#         }

#         if new_status not in valid_transitions.get(current_status, []):
#             raise HTTPException(
#                 400,
#                 f"Cannot change status from {current_status} to {new_status}"
#             )

#         # ================= CONFIRM ORDER =================
#         if new_status == "confirmed":

#             if current_status != "draft":
#                 raise HTTPException(400, "Only draft orders can be confirmed")

#             updated_items = []

#             for item in order["items"]:

#                 # 🔍 FIND ANY WAREHOUSE WITH STOCK
#                 stock = await inventory.find_one({
#                     "product_id": item["product_id"],
#                     "stock": {"$gte": item["quantity"]}
#                 })

#                 if not stock:
#                     raise HTTPException(
#                         400,
#                         f"Insufficient stock for {item['product_name']}"
#                     )

#                 # ✅ ASSIGN WAREHOUSE PER ITEM
#                 item["warehouse_id"] = stock["warehouse_id"]
#                 item["warehouse_name"] = stock["warehouse_name"]

#                 updated_items.append(item)

#             # 🔽 DEDUCT STOCK
#             for item in updated_items:
#                 await inventory.update_one(
#                     {
#                         "product_id": item["product_id"],
#                         "warehouse_id": item["warehouse_id"]
#                     },
#                     {
#                         "$inc": {"stock": -item["quantity"]}
#                     }
#                 )
          

#                 # ✅ CHECK LOW STOCK
#                 await InventoryService.check_low_stock(
#                       item["product_id"],
#                       item["warehouse_id"]
#                  )

#             # 🔁 LOG MOVEMENT
#             for item in updated_items:
#                 await logs.insert_one({
#                     "product_id": item["product_id"],
#                     "product_name": item["product_name"],
#                     "warehouse_id": item["warehouse_id"],
#                     "warehouse_name": item["warehouse_name"],
#                     "movement_type": "order_out",
#                     "quantity": item["quantity"],
#                     "timestamp": datetime.utcnow(),
#                     "remarks": f"Reserved for Order {order_id}"
#                 })

#             warehouse_names = list(set([i["warehouse_name"] for i in updated_items]))

#             # ✅ SAVE UPDATED ITEMS (with warehouse info)
#             await self.repo.update(order_id, {
#                 "items": updated_items,
#                  "warehouse_name": ", ".join(warehouse_names) 
#             })

#             order = await self.repo.get_by_id(order_id)

#             # ✅ GENERATE PDF
#             pdf_bytes = generate_invoice_pdf(order, order_id)

#              # ✅ GENERATE EMAIL
#             html_content = generate_amazon_style_email(order, order_id)

#             # print("ORDER EMAIL:", order.get("email"))

#             # ✅ SEND EMAIL
#             await send_email_with_pdf(
#                order.get("email"),
#               "🧾 Your Order Invoice",
#                html_content,
#                pdf_bytes
#             )


#         # ================= CANCEL ORDER =================
#         elif new_status == "cancelled":

#             if current_status == "cancelled":
#                 raise HTTPException(400, "Order already cancelled")

#             if current_status in ["confirmed", "packed"]:

#                 for item in order["items"]:
#                     await inventory.update_one(
#                         {
#                             "product_id": item["product_id"],
#                             "warehouse_id": item["warehouse_id"]
#                         },
#                         {
#                             "$inc": {"stock": item["quantity"]}
#                         }
#                     )

#                 for item in order["items"]:
#                     await logs.insert_one({
#                         "product_id": item["product_id"],
#                         "product_name": item["product_name"],
#                         "warehouse_id": item["warehouse_id"],
#                         "warehouse_name": item["warehouse_name"],
#                         "movement_type": "order_cancel",
#                         "quantity": item["quantity"],
#                         "timestamp": datetime.utcnow(),
#                         "remarks": f"Stock restored from cancelled Order {order_id}"
#                     })


                

#         # ================= RETURN ORDER =================
#         elif new_status == "returned":

#             if current_status != "delivered":
#                 raise HTTPException(400, "Only delivered orders can be returned")

#             for item in order["items"]:
#                 await inventory.update_one(
#                     {
#                         "product_id": item["product_id"],
#                         "warehouse_id": item["warehouse_id"]
#                     },
#                     {
#                         "$inc": {"stock": item["quantity"]}
#                     }
#                 )

#             for item in order["items"]:
#                 await logs.insert_one({
#                     "product_id": item["product_id"],
#                     "product_name": item["product_name"],
#                     "warehouse_id": item["warehouse_id"],
#                     "warehouse_name": item["warehouse_name"],
#                     "movement_type": "order_return",
#                     "quantity": item["quantity"],
#                     "timestamp": datetime.utcnow(),
#                     "remarks": f"Returned Order {order_id}"
#                 })
          
#         # ================= OTHER STATUS =================
#         # elif new_status in ["packed", "shipped", "delivered"]:
#         #     pass

#         # else:
#         #     raise HTTPException(400, "Invalid status update")

        

#         # # ✅ FINAL STATUS UPDATE
#         # await self.repo.update(order_id, {
#         #     "status": new_status,
#         #     "updated_at": datetime.utcnow()
#         # })

#         # return {"message": f"Order {new_status} successfully"}

#         elif new_status == "packed":
#             title = "Order Packed"
#             message = f"Order {order_id} has been packed"

#         elif new_status == "shipped":
#             title = "Order Shipped"
#             message = f"Order {order_id} has been shipped"

#         elif new_status == "delivered":
#             title = "Order Delivered"
#             message = f"Order {order_id} has been delivered"
 
#         elif new_status == "cancelled":
#             title = "Order Cancelled"
#             message = f"Order {order_id} has been cancelled"

#         elif new_status == "returned":
#            title = "Order Returned"
#            message = f"Order {order_id} has been returned"

      
#         await notify_admin(title, message)

#         await notify_user(
#              order["user_id"],
#              title,
#              message
#         )
from datetime import datetime
from fastapi import HTTPException, status
from bson import ObjectId
from app.core.database import db
from app.services.invoice_service import generate_invoice_pdf, generate_amazon_style_email
from app.services.email_service import send_email_with_pdf
from app.services.notification_service import NotificationService
from app.utils.notification_helper import notify_user, notify_admin
from app.services.inventory_service import InventoryService


# STATUS_EMAIL_CONFIG = {
#     "confirmed": {
#         "subject": "🧾 Your Order Invoice - Confirmed",
#         "title": "🛒 Order Confirmed",
#         "message": "Your order has been confirmed and is being prepared."
#     },
#     "packed": {
#         "subject": "📦 Your Order is Packed",
#         "title": "📦 Order Packed", 
#         "message": "Your order has been packed and is ready for shipping."
#     },
#     "shipped": {
#         "subject": "🚚 Your Order is Shipped",
#         "title": "🚚 Order Shipped",
#         "message": "Your order has been shipped. Tracking details coming soon."
#     },
#     "delivered": {
#         "subject": "✅ Order Delivered",
#         "title": "✅ Order Delivered",
#         "message": "Your order has been successfully delivered!"
#     },
#     "cancelled": {
#         "subject": "❌ Order Cancelled",
#         "title": "❌ Order Cancelled",
#         "message": "Your order has been cancelled."
#     },
#     "returned": {
#         "subject": "🔄 Order Returned",
#         "title": "🔄 Order Returned", 
#         "message": "Your order has been returned and processed."
#     }
# }


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
                stock = await inventory.find_one({
                    "product_id": item["product_id"],
                    "stock": {"$gte": item["quantity"]}
                })

                if not stock:
                    raise HTTPException(
                        400,
                        f"Insufficient stock for {item['product_name']}"
                    )

                item["warehouse_id"] = stock["warehouse_id"]
                item["warehouse_name"] = stock["warehouse_name"]

                updated_items.append(item)

            # 🔽 DEDUCT STOCK
            for item in updated_items:
                await inventory.update_one(
                    {
                        "product_id": item["product_id"],
                        "warehouse_id": item["warehouse_id"]
                    },
                    {
                        "$inc": {"stock": -item["quantity"]}
                    }
                )

                await InventoryService.check_low_stock(
                    item["product_id"],
                    item["warehouse_id"]
                )

            # 🔁 LOG MOVEMENT
            for item in updated_items:
                await logs.insert_one({
                    "product_id": item["product_id"],
                    "product_name": item["product_name"],
                    "warehouse_id": item["warehouse_id"],
                    "warehouse_name": item["warehouse_name"],
                    "movement_type": "order_out",
                    "quantity": item["quantity"],
                    "timestamp": datetime.utcnow(),
                    "remarks": f"Reserved for Order {order_id}"
                })

            warehouse_names = list(set([i["warehouse_name"] for i in updated_items]))

            await self.repo.update(order_id, {
                "items": updated_items,
                "warehouse_name": ", ".join(warehouse_names)
            })

            order = await self.repo.get_by_id(order_id)

            pdf_bytes = generate_invoice_pdf(order, order_id)
            html_content = generate_amazon_style_email(order, order_id)

            await send_email_with_pdf(
                order.get("email"),
                "🧾 Your Order Invoice",
                html_content,
                pdf_bytes
            )

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
        await notify_admin(title, message,notif_type)

        await notify_user(
            order["user_id"],
            title,
            message,
            notif_type
        )
        
        #✅ SEND STATUS EMAIL TO USER (MINIMAL ADD)
        if order.get("email"):

            subject_map = {
               "confirmed": "🧾 Order Confirmed",
               "packed": "📦 Order Packed",
              "shipped": "🚚 Order Shipped",
              "delivered": "✅ Order Delivered",
              "cancelled": "❌ Order Cancelled",
              "returned": "🔄 Order Returned"
           }

            subject = subject_map.get(new_status, "Order Update")

            html_content = generate_amazon_style_email(order, order_id)

            try:
               await send_email_with_pdf(
                  order.get("email"),
                  subject,
                  html_content
              )
            except Exception as e:
               print("Status email failed:", e)

        # ✅ FINAL STATUS UPDATE
        await self.repo.update(order_id, {
            "status": new_status,
            "updated_at": datetime.utcnow()
        })

        return {"message": f"Order {new_status} successfully"}

    # async def update_status(self, order_id, new_status):
    #     inventory = db["inventory"]
    #     logs = db["inventory_logs"]

    #     order = await self.repo.get_by_id(order_id)
    #     if not order:
    #         raise HTTPException(404, "Order not found")

    #     current_status = order.get("status")

    #     valid_transitions = {
    #        "draft": ["confirmed", "cancelled"],
    #        "confirmed": ["packed", "cancelled"],
    #        "packed": ["shipped", "cancelled"],
    #        "shipped": ["delivered"],
    #        "delivered": ["returned"],
    #         "cancelled": []
    #     }

    #     if new_status not in valid_transitions.get(current_status, []):
    #         raise HTTPException(
    #            400,
    #             f"Cannot change status from {current_status} to {new_status}"
    #     )

    # # ================= CONFIRM ORDER (KEEP YOUR EXISTING LOGIC) =================
    #     if new_status == "confirmed":
    #     # ... your existing confirmed logic stays EXACTLY the same ...
    #         if current_status != "draft":
    #            raise HTTPException(400, "Only draft orders can be confirmed")

    #         updated_items = []
    #         for item in order["items"]:
    #                 stock = await inventory.find_one({
    #                    "product_id": item["product_id"],
    #                    "stock": {"$gte": item["quantity"]}
    #             })
 
    #                 if not stock:
    #                    raise HTTPException(
    #                     400,
    #                      f"Insufficient stock for {item['product_name']}"
    #                )

    #                 item["warehouse_id"] = stock["warehouse_id"]
    #                 item["warehouse_name"] = stock["warehouse_name"]
    #                 updated_items.append(item)

    #     # 🔽 DEDUCT STOCK
    #         for item in updated_items:
    #                 await inventory.update_one(
    #                 {
    #                    "product_id": item["product_id"],
    #                    "warehouse_id": item["warehouse_id"]
    #                  },
    #                 {
    #                    "$inc": {"stock": -item["quantity"]}
    #                 }
    #             )
    #                 await InventoryService.check_low_stock(
    #                   item["product_id"],
    #                   item["warehouse_id"]
    #               )

    #     # 🔁 LOG MOVEMENT
    #         for item in updated_items:
    #                  await logs.insert_one({
    #                    "product_id": item["product_id"],
    #                    "product_name": item["product_name"],
    #                    "warehouse_id": item["warehouse_id"],
    #                     "warehouse_name": item["warehouse_name"],
    #                     "movement_type": "order_out",
    #                     "quantity": item["quantity"],
    #                     "timestamp": datetime.utcnow(),
    #                      "remarks": f"Reserved for Order {order_id}"
    #                  })

    #         warehouse_names = list(set([i["warehouse_name"] for i in updated_items]))
    #         await self.repo.update(order_id, {
    #                "items": updated_items,
    #                "warehouse_name": ", ".join(warehouse_names)
    #          })

    #         order = await self.repo.get_by_id(order_id)  # Refresh order

    #         pdf_bytes = generate_invoice_pdf(order, order_id)
    #         html_content = generate_amazon_style_email(order, order_id)
        
    #     # ✅ SEND CONFIRMATION EMAIL (existing)
    #         await send_email_with_pdf(
    #                  order.get("email"),
    #                  "🧾 Your Order Invoice",
    #                   html_content,
    #                  pdf_bytes
    #                ) 

    # # ================= CANCEL ORDER =================
    #     elif new_status == "cancelled":
    #             if current_status == "cancelled":
    #                raise HTTPException(400, "Order already cancelled")

    #             if current_status in ["confirmed", "packed"]:
    #                 for item in order["items"]:
    #                   await inventory.update_one(
    #                 {
    #                     "product_id": item["product_id"],
    #                     "warehouse_id": item["warehouse_id"]
    #                 },
    #                 {
    #                     "$inc": {"stock": item["quantity"]}
    #                 }
    #             )

    #             for item in order["items"]:
    #                await logs.insert_one({
    #                     "product_id": item["product_id"],
    #                     "product_name": item["product_name"],
    #                     "warehouse_id": item["warehouse_id"],
    #                     "warehouse_name": item["warehouse_name"],
    #                     "movement_type": "order_cancel",
    #                     "quantity": item["quantity"],
    #                     "timestamp": datetime.utcnow(),
    #                      "remarks": f"Stock restored from cancelled Order {order_id}"
    #                   })

    # # ================= RETURN ORDER =================
    #     elif new_status == "returned":
    #         if current_status != "delivered":
    #            raise HTTPException(400, "Only delivered orders can be returned")

    #         for item in order["items"]:
    #            await inventory.update_one(
    #               {
    #                 "product_id": item["product_id"],
    #                 "warehouse_id": item["warehouse_id"]
    #             },
    #             {
    #                 "$inc": {"stock": item["quantity"]}
    #             }
    #         )

    #     for item in order["items"]:
    #         await logs.insert_one({
    #             "product_id": item["product_id"],
    #             "product_name": item["product_name"],
    #             "warehouse_id": item["warehouse_id"],
    #             "warehouse_name": item["warehouse_name"],
    #             "movement_type": "order_return",
    #             "quantity": item["quantity"],
    #             "timestamp": datetime.utcnow(),
    #             "remarks": f"Returned Order {order_id}"
    #         })

    # # ================= SEND STATUS EMAIL (NEW - MINIMUM CHANGES) =================
    #     email_config = STATUS_EMAIL_CONFIG.get(new_status)
    #     if email_config and order.get("email"):
    #     # Generate status-specific HTML (reuse your existing function)
    #         html_content = generate_amazon_style_email(order, order_id)
        
    #     # For confirmed orders, we already sent PDF above
    #         pdf_bytes = None
    #         if new_status == "confirmed":
    #             pdf_bytes = generate_invoice_pdf(order, order_id)
        
    #         await send_email_with_pdf(
    #            order.get("email"),
    #            email_config["subject"],
    #            html_content,
    #            pdf_bytes  # None for non-confirmed statuses
    #       )

    # # ================= STATUS MESSAGES & NOTIFICATIONS (KEEP EXISTING) =================
    #     product_names = [item["product_name"] for item in order["items"]]
    #     product_text = ", ".join([
    #         f"{item['product_name']} (x{item['quantity']})"
    #         for item in order["items"][:2]
    #      ])
    #     if len(product_names) > 2:
    #        product_text += "..." 

    #     if new_status == "confirmed":
    #        title = "Order Confirmed"
    #        message = f"{product_text} confirmed (Order #{order_id})"
    #     elif new_status == "packed":
    #        title = "Order Packed"
    #        message = f"{product_text} packed (Order #{order_id})"
    #     elif new_status == "shipped":
    #        title = "Order Shipped"
    #        message = f"{product_text} shipped (Order #{order_id})"
    #     elif new_status == "delivered":
    #        title = "Order Delivered"
    #        message = f"{product_text} delivered (Order #{order_id})"
    #     elif new_status == "cancelled":
    #        title = "Order Cancelled"
    #        message = f"{product_text} cancelled (Order #{order_id})"
    #     elif new_status == "returned":
    #        title = "Order Returned"
    #        message = f"{product_text} returned (Order #{order_id})"
    #     else:
    #       title = "Order Update"
    #       message = f"{product_text} updated to {new_status} (Order #{order_id})"

    #     if new_status == "confirmed":
    #        notif_type = "order_confirmed"
    #     elif new_status == "cancelled":
    #        notif_type = "order_cancelled"
    #     else:
    #        notif_type = "order_update"

    # # ✅ NOTIFICATIONS
    #     await notify_admin(title, message, notif_type)
    #     await notify_user(
    #        order["user_id"],
    #        title,
    #        message,
    #        notif_type
    #    )

    # # ✅ FINAL STATUS UPDATE
    #     await self.repo.update(order_id, {
    #       "status": new_status,
    #       "updated_at": datetime.utcnow()
    #     })

    #     return {"message": f"Order {new_status} successfully"}

   