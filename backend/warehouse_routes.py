from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId
from database import warehouse_collection, users_collection, products_collection
from models import Warehouse, AssignStaff
from deps import get_current_user

router = APIRouter()

# ---------------- CREATE WAREHOUSE ----------------
@router.post("/warehouse")
async def create_warehouse(data: Warehouse):
    existing = await warehouse_collection.find_one({"code": data.code})
    if existing:
        raise HTTPException(status_code=400, detail="Warehouse code exists")

    warehouse = data.dict()
    warehouse["staff_ids"] = []
    warehouse["manager_id"] = None
    warehouse["inventory"] = []

    result = await warehouse_collection.insert_one(warehouse)
    return {"message": "Warehouse created", "id": str(result.inserted_id)}


# ---------------- ASSIGN USER ----------------
@router.post("/warehouse/assign")
async def assign_staff(data: AssignStaff):

    user = await users_collection.find_one({"_id": ObjectId(data.user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user["role"] == "inventory_manager":
        await warehouse_collection.update_one(
            {"_id": ObjectId(data.warehouse_id)},
            {"$set": {"manager_id": data.user_id}}
        )

    elif user["role"] == "warehouse_staff":
        await warehouse_collection.update_one(
            {"_id": ObjectId(data.warehouse_id)},
            {"$addToSet": {"staff_ids": data.user_id}}
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid role")

    # 🔥 LINK USER TO WAREHOUSE
    await users_collection.update_one(
        {"_id": ObjectId(data.user_id)},
        {"$set": {"warehouse_id": data.warehouse_id}}
    )

    return {"message": "Assigned successfully"}


# ---------------- GET WAREHOUSES (RBAC) ----------------
@router.get("/warehouse")
async def get_warehouses(current_user: dict = Depends(get_current_user)):

    if current_user["role"] == "admin":
        query = {}

    elif current_user["role"] in ["inventory_manager", "warehouse_staff"]:
        if not current_user.get("warehouse_id"):
            return []
        query = {"_id": ObjectId(current_user["warehouse_id"])}

    else:
        return []

    data = await warehouse_collection.find(query).to_list(100)

    for w in data:
        w["_id"] = str(w["_id"])

        # MANAGER
        if w.get("manager_id"):
            manager = await users_collection.find_one({"_id": ObjectId(w["manager_id"])})
            if manager:
                w["manager"] = {
                    "id": str(manager["_id"]),
                    "name": manager["name"]
                }

        # STAFF
        staff_list = []
        for sid in w.get("staff_ids", []):
            staff = await users_collection.find_one({"_id": ObjectId(sid)})
            if staff:
                staff_list.append({
                    "id": str(staff["_id"]),
                    "name": staff["name"],
                    "email": staff.get("email")
                })
        w["staff"] = staff_list

        # INVENTORY
        inventory_list = []
        for item in w.get("inventory", []):
            product = await products_collection.find_one({"variants.sku": item["sku"]})

            if product:
                for v in product["variants"]:
                    if v["sku"] == item["sku"]:
                        inventory_list.append({
                            "sku": v["sku"],
                            "quantity": item["quantity"],
                            "stock": v.get("stock", 0),
                            "product_name": product.get("name"),
                            "image": product.get("image"), 
                            "price": v.get("price")
                        })

        w["inventory"] = inventory_list

    return data


# ---------------- ADD INVENTORY ----------------

@router.post("/warehouse/inventory/add")
async def add_inventory(data: dict, current_user: dict = Depends(get_current_user)):

    if current_user["role"] not in ["admin", "inventory_manager"]:
        raise HTTPException(status_code=403, detail="Not allowed")

    warehouse_id = ObjectId(str(data["warehouse_id"]))

    warehouse = await warehouse_collection.find_one({"_id": warehouse_id})
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")

    sku = data["sku"]
    qty = int(data["quantity"])

    inventory = warehouse.get("inventory", [])

    found = False

    for item in inventory:
        if item["sku"] == sku:
            item["quantity"] += qty
            found = True
            break

    if not found:
        inventory.append({
            "sku": sku,
            "quantity": qty
        })

    await warehouse_collection.update_one(
        {"_id": warehouse_id},
        {"$set": {"inventory": inventory}}
    )

    # update global stock
    await products_collection.update_one(
        {"variants.sku": sku},
        {"$inc": {"variants.$.stock": qty}}
    )

    return {"message": "Inventory added"}



# ---------------- TRANSFER INVENTORY ----------------
@router.post("/warehouse/inventory/transfer")
async def transfer_inventory(data: dict, current_user: dict = Depends(get_current_user)):

    # ================= RBAC =================
    if current_user["role"] not in ["admin", "inventory_manager"]:
        raise HTTPException(status_code=403, detail="Not allowed")

    from_id = data.get("from_warehouse")
    to_id = data.get("to_warehouse")
    sku = data.get("sku")
    qty = data.get("quantity")

    # ================= VALIDATION =================
    if not from_id or not to_id or not sku or not qty:
        raise HTTPException(status_code=400, detail="All fields required")

    if from_id == to_id:
        raise HTTPException(status_code=400, detail="Cannot transfer to same warehouse")

    if qty <= 0:
        raise HTTPException(status_code=400, detail="Invalid quantity")

    # ================= FETCH =================
    from_wh = await warehouse_collection.find_one({"_id": ObjectId(from_id)})
    to_wh = await warehouse_collection.find_one({"_id": ObjectId(to_id)})

    if not from_wh or not to_wh:
        raise HTTPException(status_code=404, detail="Warehouse not found")

    # ================= CHECK SKU IN SOURCE =================
    source_inventory = from_wh.get("inventory", [])

    source_item = None
    for item in source_inventory:
        if item["sku"] == sku:
            source_item = item
            break

    if not source_item:
        raise HTTPException(status_code=404, detail="SKU not found in source warehouse")

    if source_item["quantity"] < qty:
        raise HTTPException(status_code=400, detail="Not enough stock in source")

    # ================= REMOVE FROM SOURCE =================
    source_item["quantity"] -= qty

    # remove item if becomes 0
    if source_item["quantity"] == 0:
        source_inventory = [i for i in source_inventory if i["sku"] != sku]

    # ================= ADD TO DESTINATION =================
    dest_inventory = to_wh.get("inventory", [])

    dest_item = None
    for item in dest_inventory:
        if item["sku"] == sku:
            dest_item = item
            break

    if dest_item:
        dest_item["quantity"] += qty
    else:
        dest_inventory.append({
            "sku": sku,
            "quantity": qty
        })

    # ================= SAVE BOTH =================
    await warehouse_collection.update_one(
        {"_id": ObjectId(from_id)},
        {"$set": {"inventory": source_inventory}}
    )

    await warehouse_collection.update_one(
        {"_id": ObjectId(to_id)},
        {"$set": {"inventory": dest_inventory}}
    )

    return {
        "message": "Transfer successful",
        "sku": sku,
        "moved": qty,
        "from": from_id,
        "to": to_id
    }

@router.post("/warehouse/inventory/delete")
async def delete_inventory(data: dict, current_user: dict = Depends(get_current_user)):

    if current_user["role"] not in ["admin", "inventory_manager"]:
        raise HTTPException(status_code=403, detail="Not allowed")

    await warehouse_collection.update_one(
        {"_id": ObjectId(data["warehouse_id"])},
        {"$pull": {"inventory": {"sku": data["sku"]}}}
    )

    return {"message": "Inventory removed"}