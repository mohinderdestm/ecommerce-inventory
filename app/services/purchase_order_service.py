from fastapi import HTTPException
from datetime import datetime
from bson import ObjectId
from app.core.database import db
from app.services.audit_service import AuditService


class PurchaseService:
    def __init__(self, repo):
        self.repo = repo

    # ✅ CREATE PO
    async def create_po(self, data,user):
        payload = data.dict()

        for item in payload["items"]:
            item["received_quantity"] = 0

        payload["status"] = "draft"
        payload["created_at"] = datetime.utcnow()
        payload["updated_at"] = datetime.utcnow()

        result = await self.repo.create(payload)
        
        await AuditService.log(
            user_id=str(user["_id"]),
            action="PO_CREATED",
            entity_type="purchase_order",
            entity_id=str(result),
            value=payload
        )

        return {"id": result}

    # ✅ LIST PO
    async def list_po(self):
        data = await self.repo.get_all()

        result = []
        for po in data:
            po["id"] = str(po["_id"])
            del po["_id"]
            result.append(po)

        return result

    # ✅ UPDATE STATUS
    async def update_status(self, po_id, new_status,user):
        po = await self.repo.get_by_id(po_id)

        if not po:
            raise HTTPException(404, "PO not found")

        current = po["status"]

        if new_status == "submitted" and current != "draft":
            raise HTTPException(400, "Only draft can be submitted")

        if new_status == "approved" and current != "submitted":
            raise HTTPException(400, "Only submitted can be approved")

        if new_status == "rejected" and current != "submitted":
            raise HTTPException(400, "Only submitted can be rejected")

        await self.repo.update(po_id, {
            "status": new_status,
            "updated_at": datetime.utcnow()
        })
        
        await AuditService.log(
            user_id=str(user["_id"]),
            action=f"PO_{new_status.upper()}",
            entity_type="purchase_order",
            entity_id=po_id,
            old_value={
               "status": current,
               "items": po.get("items"),
               "supplier_id": po.get("supplier_id")
            },
            new_value={
              "status": new_status
            }
        )

        return {"message": f"PO {new_status} successfully"}

    

    async def receive_items(self, po_id, payload,user):

        po = await self.repo.get_by_id(po_id)

        if not po:
           raise HTTPException(404, "PO not found")

        inventory = self.repo.collection.database["inventory"]
        logs = self.repo.collection.database["inventory_logs"]
        for incoming_item in payload.items:  

               for item in po["items"]:
                    if item["product_id"] == incoming_item.product_id:
                        ordered = item.get("quantity", 0)
                        received = item.get("received_quantity", 0)

                        received_qty = incoming_item.quantity 

                        new_received = received + received_qty

        # ❌ prevent over receive
                        if new_received > ordered:
                            raise HTTPException(400, "Receiving more than ordered")

        # ✅ UPDATE ITEM
                        item["received_quantity"] = new_received

                        await inventory.update_one(
                            {
                                "product_id": item["product_id"],
                                "warehouse_id": po["warehouse_id"]
                            },
                            {
                                "$inc": {"stock": received_qty},
                                "$set": {
                                     "product_name": item.get("product_name"),
                                     "category": item.get("category", "General")
                                }
                            },
                            upsert=True
                      )
                        

           # ✅ STATUS FIX
        all_received = all(
          i.get("received_quantity", 0) == i.get("quantity", 0)
          for i in po["items"]
      )

        status = "completed" if all_received else "partially_received"
        
        await AuditService.log(
            user_id=str(user["_id"]),
            action="PO_ITEMS_RECEIVED",
            entity_type="purchase_order",
            entity_id=po_id,
            value={
            "received_items": [i.dict() for i in payload.items],
            "status": status
             }
                )


        # ✅ LOG
        await logs.insert_one({
              "product_id": item["product_id"],
              "product_name": item["product_name"],
              "warehouse_id": po["warehouse_id"],
              "warehouse_name": po["warehouse_name"],
              "movement_type": "purchase_in",
              "quantity": received_qty,
              "timestamp": datetime.utcnow(),
              "remarks": f"Received from PO {po_id}"
        })

    # # ✅ STATUS LOGIC (IMPORTANT FIX)
    #     all_received = all(
    #        i.get("received_quantity", 0) == i.get("quantity", 0)
    #        for i in po["items"]
    #     )

    #     if all_received:
    #        status = "completed"
    #     else:
    #        status = "partially_received"

    # ✅ SAVE BACK TO DB (CRITICAL)
        await self.repo.update(po_id, {
           "items": po["items"],
           "status": status,
           "updated_at": datetime.utcnow()
        })

        return {"message": f"PO {status}"}


    async def attach_invoice(self, po_id, invoice_number, invoice_date,user):

    # ✅ AUTO GENERATE if empty
        if not invoice_number or invoice_number == "null":
          invoice_number = f"INV-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        await self.repo.update(po_id, {
          "invoice_number": invoice_number,
           "invoice_date": invoice_date
       })
        
        await AuditService.log(
            user_id=str(user["_id"]),
            action="PO_INVOICE_ADDED",
            entity_type="purchase_order",
            entity_id=po_id,
            value={
                "invoice_number": invoice_number,
                "invoice_date": str(invoice_date)
            }
         )

        return {"message": "Invoice generated", "invoice_number": invoice_number}
