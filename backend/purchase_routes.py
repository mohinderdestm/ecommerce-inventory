from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from datetime import datetime
from database import purchase_collection, products_collection, warehouse_collection
from deps import get_current_user

router = APIRouter()

VALID_STATUSES = [
    "draft",
    "submitted",
    "approved",
    "rejected",
    "cancelled",
    "received"
]


# ================= CREATE PO =================
@router.post("/purchase")
async def create_po(data: dict, user=Depends(get_current_user)):

    if user["role"] not in ["admin", "inventory_manager"]:
        raise HTTPException(status_code=403, detail="Not allowed")

    if not data.get("warehouse_id"):
        raise HTTPException(status_code=400, detail="Warehouse required")

    if not data.get("supplier_email"):
        raise HTTPException(status_code=400, detail="Supplier required")

    if not data.get("items") or len(data["items"]) == 0:
        raise HTTPException(status_code=400, detail="Items required")

    po = {
        "warehouse_id": data["warehouse_id"],
        "supplier_email": data["supplier_email"],
        "items": data["items"],
        "status": "draft",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    result = await purchase_collection.insert_one(po)

    return {
        "message": "PO created",
        "id": str(result.inserted_id)
    }


# ================= GET PURCHASE ORDERS =================
@router.get("/purchase")
async def get_po(user=Depends(get_current_user)):

    data = await purchase_collection.find().sort(
        "created_at", -1
    ).to_list(100)

    for po in data:
        po["_id"] = str(po["_id"])

    return data


# ================= UPDATE STATUS =================
@router.put("/purchase/status/{po_id}")
async def update_po_status(
    po_id: str,
    data: dict,
    user=Depends(get_current_user)
):

    if user["role"] not in ["admin", "inventory_manager"]:
        raise HTTPException(status_code=403, detail="Not allowed")

    new_status = data.get("status")

    if new_status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail="Invalid status"
        )

    po = await purchase_collection.find_one({
        "_id": ObjectId(po_id)
    })

    if not po:
        raise HTTPException(
            status_code=404,
            detail="PO not found"
        )

    current_status = po.get("status")

    # Prevent editing completed orders
    if current_status == "received":
        raise HTTPException(
            status_code=400,
            detail="Received PO cannot be changed"
        )

    # ================= RECEIVED STATUS =================
    # When received → add inventory into warehouse

    if new_status == "received" and current_status != "received":

        warehouse_id = ObjectId(
            str(po["warehouse_id"])
        )

        warehouse = await warehouse_collection.find_one({
            "_id": warehouse_id
        })

        if not warehouse:
            raise HTTPException(
                status_code=404,
                detail="Warehouse not found"
            )

        inventory = warehouse.get("inventory", [])

        for item in po["items"]:

            sku = item["sku"]
            qty = int(item["quantity"])

            found = False

            for inv in inventory:
                if inv["sku"] == sku:
                    inv["quantity"] += qty
                    found = True
                    break

            if not found:
                inventory.append({
                    "sku": sku,
                    "quantity": qty
                })

            # update global stock
            await products_collection.update_one(
                {"variants.sku": sku},
                {"$inc": {"variants.$.stock": qty}}
            )

        await warehouse_collection.update_one(
            {"_id": warehouse_id},
            {"$set": {"inventory": inventory}}
        )

    await purchase_collection.update_one(
        {"_id": ObjectId(po_id)},
        {
            "$set": {
                "status": new_status,
                "updated_at": datetime.utcnow()
            }
        }
    )

    return {
        "message": f"PO status updated to {new_status}"
    }