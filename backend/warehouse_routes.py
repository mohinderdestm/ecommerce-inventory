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
                    "name": staff["name"]
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
                            "stock": v.get("stock", 0)
                        })

        w["inventory"] = inventory_list

    return data


# ---------------- ADD INVENTORY ----------------
@router.post("/warehouse/inventory/add")
async def add_inventory(data: dict, current_user: dict = Depends(get_current_user)):

    # 🔥 RBAC FIX
    if current_user["role"] not in ["admin", "inventory_manager"]:
        raise HTTPException(status_code=403, detail="Not allowed")

    if current_user["role"] != "admin":
        if str(current_user.get("warehouse_id")) != data["warehouse_id"]:
            raise HTTPException(status_code=403, detail="Unauthorized warehouse")

    warehouse = await warehouse_collection.find_one({"_id": ObjectId(data["warehouse_id"])})
    if not warehouse:
        raise HTTPException(status_code=404, detail="Warehouse not found")

    # FIND VARIANT
    product = await products_collection.find_one({"variants.sku": data["sku"]})
    if not product:
        raise HTTPException(status_code=404, detail="Invalid SKU")

    inventory = warehouse.get("inventory", [])

    found = False
    for item in inventory:
        if item["sku"] == data["sku"]:
            item["quantity"] += data["quantity"]
            found = True
            break

    if not found:
        inventory.append({
            "sku": data["sku"],
            "quantity": data["quantity"]
        })

    await warehouse_collection.update_one(
        {"_id": ObjectId(data["warehouse_id"])},
        {"$set": {"inventory": inventory}}
    )

    # UPDATE GLOBAL STOCK
    await products_collection.update_one(
        {"_id": product["_id"], "variants.sku": data["sku"]},
        {"$inc": {"variants.$.stock": data["quantity"]}}
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





# from fastapi import APIRouter, HTTPException,Depends
# from bson import ObjectId
# from database import warehouse_collection, users_collection, products_collection
# from models import Warehouse, AssignStaff
# from deps import get_current_user


# router = APIRouter()

# # ---------------- CREATE WAREHOUSE ----------------
# @router.post("/warehouse")
# async def create_warehouse(data: Warehouse):
#     existing = await warehouse_collection.find_one({"code": data.code})
#     if existing:
#         raise HTTPException(status_code=400, detail="Warehouse code exists")

#     warehouse = data.dict()
#     warehouse["staff_ids"] = []
#     warehouse["manager_id"] = None

#     result = await warehouse_collection.insert_one(warehouse)
#     return {"message": "Warehouse created", "id": str(result.inserted_id)}

# @router.post("/warehouse/assign")
# async def assign_staff(data: AssignStaff):

#     user = await users_collection.find_one({"_id": ObjectId(data.user_id)})
#     if not user:
#         return {"error": "User not found"}

#     # ================= MANAGER =================
#     if user["role"] == "inventory_manager":

#         await warehouse_collection.update_one(
#             {"_id": ObjectId(data.warehouse_id)},
#             {"$set": {"manager_id": data.user_id}}
#         )

#         # ⭐ VERY IMPORTANT (THIS WAS MISSING)
#         await users_collection.update_one(
#             {"_id": ObjectId(data.user_id)},
#             {"$set": {"warehouse_id": data.warehouse_id}}
#         )

#     # ================= STAFF =================
#     elif user["role"] == "warehouse_staff":

#         await warehouse_collection.update_one(
#             {"_id": ObjectId(data.warehouse_id)},
#             {"$addToSet": {"staff_ids": data.user_id}}
#         )

#         # ⭐ VERY IMPORTANT (THIS WAS MISSING)
#         await users_collection.update_one(
#             {"_id": ObjectId(data.user_id)},
#             {"$set": {"warehouse_id": data.warehouse_id}}
#         )

#     else:
#         return {"error": "Invalid role"}

#     return {"message": "Assigned successfully"}

    



# @router.get("/warehouse")
# async def get_warehouses(current_user: dict = Depends(get_current_user)):

#     if current_user["role"] == "admin":
#         query = {}

#     elif current_user["role"] in ["inventory_manager", "warehouse_staff"]:
#         if not current_user.get("warehouse_id"):
#             return []  # no warehouse assigned

#         query = {"_id": ObjectId(current_user["warehouse_id"])}

#     else:
#         return [] 

    

#     data = await warehouse_collection.find(query).to_list(100)

#     for w in data:
#         w["_id"] = str(w["_id"])

#         if w.get("manager_id"):
#             manager = await users_collection.find_one({
#                 "_id": ObjectId(w["manager_id"])
#             })

#             if manager:
#                 w["manager"] = {
#                     "id": str(manager["_id"]),
#                     "name": manager.get("name"),
#                     "email": manager.get("email")
#                 }
#             else:
#                 w["manager"] = None
#         else:
#             w["manager"] = None

#         # ================= STAFF =================
#         staff_list = []

#         for sid in w.get("staff_ids", []):
#             staff = await users_collection.find_one({
#                 "_id": ObjectId(sid)
#             })

#             if staff:
#                 staff_list.append({
#                     "id": str(staff["_id"]),
#                     "name": staff.get("name"),
#                     "email": staff.get("email")
#                 })

#         w["staff"] = staff_list

#         inventory_list = []

#         for item in w.get("inventory", []):

#             product = await products_collection.find_one({
#                 "variants.sku": item["sku"]
#             })

#             if product:
#                 for v in product["variants"]:
#                     if v["sku"] == item["sku"]:
#                         inventory_list.append({
#                             "sku": v["sku"],
#                             "quantity": item["quantity"],       # warehouse qty
#                             "stock": v.get("stock", 0)          # 🔥 TOTAL STOCK
#                         })

#         w["inventory"] = inventory_list

#     return data

# @router.post("/warehouse/inventory/add")
# async def add_inventory(data: dict,    current_user: dict = Depends(get_current_user)):
#     if current_user["role"] == "viewer":
#         raise HTTPException(status_code=403, detail="No permission")

#     # ❌ BLOCK WRONG WAREHOUSE
#     if current_user["role"] != "admin":
#         if str(current_user.get("warehouse_id")) != data["warehouse_id"]:
#             raise HTTPException(status_code=403, detail="Unauthorized warehouse")

#     warehouse = await warehouse_collection.find_one(
#         {"_id": ObjectId(data["warehouse_id"])}
#     )
#     if not warehouse:
#         raise HTTPException(status_code=404, detail="Warehouse not found")

#     # 🔥 FIND VARIANT INSIDE PRODUCTS
#     product = await products_collection.find_one({
#         "variants.sku": data["sku"]
#     })

#     if not product:
#         raise HTTPException(status_code=404, detail="Invalid SKU")

#     # 🔥 FIND VARIANT INDEX
#     variant_index = None
#     for i, v in enumerate(product["variants"]):
#         if v["sku"] == data["sku"]:
#             variant_index = i
#             break

#     if variant_index is None:
#         raise HTTPException(status_code=404, detail="Variant not found")

#     # ================== UPDATE WAREHOUSE ==================
#     inventory = warehouse.get("inventory", [])

#     found = False
#     for item in inventory:
#         if item["sku"] == data["sku"]:
#             item["quantity"] += data["quantity"]
#             found = True
#             break

#     if not found:
#         inventory.append({
#             "sku": data["sku"],
#             "quantity": data["quantity"]
#         })

#     await warehouse_collection.update_one(
#         {"_id": ObjectId(data["warehouse_id"])},
#         {"$set": {"inventory": inventory}}
#     )

#     # ================== UPDATE VARIANT STOCK ==================
#     await products_collection.update_one(
#         {"_id": product["_id"], "variants.sku": data["sku"]},
#         {"$inc": {"variants.$.stock": data["quantity"]}}
#     )

#     return {"message": "Inventory + Variant stock updated"}

# @router.get("/warehouse/{warehouse_id}/inventory")
# async def get_inventory(warehouse_id: str):

#     warehouse = await warehouse_collection.find_one(
#         {"_id": ObjectId(warehouse_id)}
#     )

#     if not warehouse:
#         raise HTTPException(status_code=404, detail="Warehouse not found")

#     return {
#         "warehouse": str(warehouse["_id"]),
#         "inventory": warehouse.get("inventory", [])
#     }