from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from database import products_collection, orders_collection
from deps import get_current_user
import datetime

router = APIRouter(prefix="/orders", tags=["Orders"])

VALID_STATUS = [
    "Draft", "Confirmed", "Packed",
    "Shipped", "Delivered",
    "Cancelled", "Returned"
]

def serialize_order(d):
    return {
        "id": str(d["_id"]),
        "user_email": d.get("user_email"),
        "status": d.get("status"),
        "items": d.get("items", []),
        "total": d.get("total", 0),
        "created_at": d.get("created_at")
    }

# ✅ CREATE ORDER
@router.post("")
async def create_order(user=Depends(get_current_user)):
    order = {
        "user_email": user["email"],
        "status": "Draft",
        "items": [],
        "total": 0,
        "created_at": datetime.datetime.utcnow().isoformat()
    }

    res = await orders_collection.insert_one(order)

    return {
        "data": {
            "id": str(res.inserted_id),
            "user_email": order["user_email"],
            "status": order["status"],
            "items": [],
            "total": 0,
            "created_at": order["created_at"]
        }
    }


# ✅ ADD ITEM (VARIANT ONLY)
@router.post("/{order_id}/add")
async def add_item(order_id: str, data: dict, user=Depends(get_current_user)):
    order = await orders_collection.find_one({"_id": ObjectId(order_id)})

    if not order:
        raise HTTPException(status_code=404)

    if order["status"] != "Draft":
        raise HTTPException(status_code=400, detail="Not editable")

    if not data.get("variant_id"):
        raise HTTPException(status_code=400, detail="Variant required")

    product = await products_collection.find_one({"_id": ObjectId(data["product_id"])})

    variant = next((v for v in product["variants"] if v["id"] == data["variant_id"]), None)

    if not variant:
        raise HTTPException(status_code=404)

    if variant["stock"] < data["quantity"]:
        raise HTTPException(status_code=400, detail="Insufficient stock")

    item = {
        "product_id": data["product_id"],
        "variant_id": data["variant_id"],
        "product_name": product["name"],
        "supplier_email": product["supplier_email"],
        "color": variant["color"],
        "size": variant["size"],
        "price": variant["price"],
        "quantity": data["quantity"]
    }

    new_total = order["total"] + variant["price"] * data["quantity"]

    await orders_collection.update_one(
        {"_id": ObjectId(order_id)},
        {
            "$push": {"items": item},
            "$set": {"total": new_total}
        }
    )

    return {"message": "Item added"}


# ✅ CONFIRM ORDER (STOCK DEDUCT)
@router.post("/{order_id}/confirm")
async def confirm_order(order_id: str, user=Depends(get_current_user)):
    order = await orders_collection.find_one({"_id": ObjectId(order_id)})

    if not order:
        raise HTTPException(status_code=404)

    if order["status"] != "Draft":
        raise HTTPException(status_code=400)

    for item in order["items"]:
        product = await products_collection.find_one({"_id": ObjectId(item["product_id"])})

        for v in product["variants"]:
            if v["id"] == item["variant_id"]:
                if v["stock"] < item["quantity"]:
                    raise HTTPException(status_code=400, detail="Stock changed")

                v["stock"] -= item["quantity"]

        await products_collection.update_one(
            {"_id": ObjectId(item["product_id"])},
            {"$set": {"variants": product["variants"]}}
        )

    await orders_collection.update_one(
        {"_id": ObjectId(order_id)},
        {"$set": {"status": "Confirmed"}}
    )

    return {"message": "Confirmed"}


# ✅ STATUS UPDATE (RBAC)
@router.put("/{order_id}/status")
async def update_status(order_id: str, data: dict, user=Depends(get_current_user)):
    if data["status"] not in VALID_STATUS:
        raise HTTPException(status_code=400)

    # RBAC
    if user["role"] == "admin":
        pass
    elif user["role"] == "supplier":
        if data["status"] not in ["Packed", "Shipped"]:
            raise HTTPException(status_code=403)
    else:
        raise HTTPException(status_code=403)

    await orders_collection.update_one(
        {"_id": ObjectId(order_id)},
        {"$set": {"status": data["status"]}}
    )

    return {"message": "Updated"}


# ✅ CANCEL
@router.post("/{order_id}/cancel")
async def cancel_order(order_id: str, user=Depends(get_current_user)):
    order = await orders_collection.find_one({"_id": ObjectId(order_id)})

    if not order:
        raise HTTPException(status_code=404)

    # ✅ RBAC RULES
    if user["role"] == "viewer":
        if order["user_email"] != user["email"]:
            raise HTTPException(status_code=403)

        # ❌ viewer can cancel only Draft
        if order["status"] != "Draft":
            raise HTTPException(status_code=400, detail="Cannot cancel after confirmation")

    elif user["role"] == "supplier":
        raise HTTPException(status_code=403)

    # admin can always cancel

    # ✅ restore stock
    for item in order["items"]:
        product = await products_collection.find_one({"_id": ObjectId(item["product_id"])})

        for v in product["variants"]:
            if v["id"] == item["variant_id"]:
                v["stock"] += item["quantity"]

        await products_collection.update_one(
            {"_id": ObjectId(item["product_id"])},
            {"$set": {"variants": product["variants"]}}
        )

    await orders_collection.update_one(
        {"_id": ObjectId(order_id)},
        {"$set": {"status": "Cancelled"}}
    )

    return {"message": "Cancelled"}


# ✅ GET ORDERS (RBAC)
@router.get("")
async def get_orders(user=Depends(get_current_user)):
    data = []

    if user["role"] == "admin":
        data = await orders_collection.find().to_list(1000)

    elif user["role"] == "supplier":
        all_orders = await orders_collection.find().to_list(1000)

        for o in all_orders:
            items = [i for i in o["items"] if i["supplier_email"] == user["email"]]
            if items:
                o["items"] = items
                data.append(o)

    else:
        data = await orders_collection.find({
            "user_email": user["email"]
        }).to_list(1000)

    # ✅ SAFE SERIALIZATION
    return {"data": [serialize_order(d) for d in data]}



# from fastapi import APIRouter, Depends, HTTPException
# from bson import ObjectId
# from database import products_collection, orders_collection
# from deps import get_current_user
# import datetime

# router = APIRouter(prefix="/orders", tags=["Orders"])

# VALID_STATUS = [
#     "Draft", "Confirmed", "Packed",
#     "Shipped", "Delivered",
#     "Cancelled", "Returned"
# ]


# # ✅ CREATE ORDER
# @router.post("")
# async def create_order(user=Depends(get_current_user)):
#     order = {
#         "user_email": user["email"],
#         "status": "Draft",
#         "items": [],
#         "total": 0,
#         "created_at": datetime.datetime.utcnow().isoformat()
#     }

#     res = await orders_collection.insert_one(order)

#     # ✅ FIX RESPONSE
#     return {
#         "data": {
#             "id": str(res.inserted_id),
#             "user_email": order["user_email"],
#             "status": order["status"],
#             "items": [],
#             "total": 0,
#             "created_at": order["created_at"]
#         }
#     }


# # ✅ ADD ITEM
# @router.post("/{order_id}/add")
# async def add_item(order_id: str, data: dict, user=Depends(get_current_user)):
#     order = await orders_collection.find_one({"_id": ObjectId(order_id)})

#     if not order:
#         raise HTTPException(status_code=404)

#     if order["status"] != "Draft":
#         raise HTTPException(status_code=400, detail="Not editable")

#     product = await products_collection.find_one({"_id": ObjectId(data["product_id"])})
#     if not product:
#         raise HTTPException(status_code=404)

#     variant = next((v for v in product["variants"] if v["id"] == data["variant_id"]), None)

#     if not variant:
#         raise HTTPException(status_code=404)

#     if variant["stock"] < data["quantity"]:
#         raise HTTPException(status_code=400, detail="Insufficient stock")

#     item = {
#         "product_id": data["product_id"],
#         "variant_id": data["variant_id"],
#         "supplier_email": product["supplier_email"],
#         "color": variant["color"],
#         "size": variant["size"],
#         "price": variant["price"],
#         "quantity": data["quantity"]
#     }

#     new_total = order["total"] + variant["price"] * data["quantity"]

#     await orders_collection.update_one(
#         {"_id": ObjectId(order_id)},
#         {
#             "$push": {"items": item},
#             "$set": {"total": new_total}
#         }
#     )

#     return {"message": "Item added"}


# # ✅ CONFIRM ORDER (RESERVE STOCK)
# @router.post("/{order_id}/confirm")
# async def confirm_order(order_id: str):
#     order = await orders_collection.find_one({"_id": ObjectId(order_id)})

#     if not order:
#         raise HTTPException(status_code=404)

#     if order["status"] != "Draft":
#         raise HTTPException(status_code=400)

#     # validate + deduct
#     for item in order["items"]:
#         product = await products_collection.find_one({"_id": ObjectId(item["product_id"])})

#         for v in product["variants"]:
#             if v["id"] == item["variant_id"]:
#                 if v["stock"] < item["quantity"]:
#                     raise HTTPException(status_code=400, detail="Stock changed")

#                 v["stock"] -= item["quantity"]

#         await products_collection.update_one(
#             {"_id": ObjectId(item["product_id"])},
#             {"$set": {"variants": product["variants"]}}
#         )

#     await orders_collection.update_one(
#         {"_id": ObjectId(order_id)},
#         {"$set": {"status": "Confirmed"}}
#     )

#     return {"message": "Confirmed"}


# # ✅ STATUS UPDATE
# @router.put("/{order_id}/status")
# async def update_status(order_id: str, data: dict):
#     if data["status"] not in VALID_STATUS:
#         raise HTTPException(status_code=400)

#     await orders_collection.update_one(
#         {"_id": ObjectId(order_id)},
#         {"$set": {"status": data["status"]}}
#     )

#     return {"message": "Updated"}


# # ✅ CANCEL (RESTORE STOCK)
# @router.post("/{order_id}/cancel")
# async def cancel_order(order_id: str):
#     order = await orders_collection.find_one({"_id": ObjectId(order_id)})

#     if not order:
#         raise HTTPException(status_code=404)

#     for item in order["items"]:
#         product = await products_collection.find_one({"_id": ObjectId(item["product_id"])})

#         for v in product["variants"]:
#             if v["id"] == item["variant_id"]:
#                 v["stock"] += item["quantity"]

#         await products_collection.update_one(
#             {"_id": ObjectId(item["product_id"])},
#             {"$set": {"variants": product["variants"]}}
#         )

#     await orders_collection.update_one(
#         {"_id": ObjectId(order_id)},
#         {"$set": {"status": "Cancelled"}}
#     )

#     return {"message": "Cancelled"}


# # ✅ RETURN
# @router.post("/{order_id}/return")
# async def return_order(order_id: str):
#     order = await orders_collection.find_one({"_id": ObjectId(order_id)})

#     if order["status"] != "Delivered":
#         raise HTTPException(status_code=400)

#     for item in order["items"]:
#         product = await products_collection.find_one({"_id": ObjectId(item["product_id"])})

#         for v in product["variants"]:
#             if v["id"] == item["variant_id"]:
#                 v["stock"] += item["quantity"]

#         await products_collection.update_one(
#             {"_id": ObjectId(item["product_id"])},
#             {"$set": {"variants": product["variants"]}}
#         )

#     await orders_collection.update_one(
#         {"_id": ObjectId(order_id)},
#         {"$set": {"status": "Returned"}}
#     )

#     return {"message": "Returned"}


# # ✅ GET ORDERS (RBAC)
# @router.get("")
# async def get_orders(user=Depends(get_current_user)):
#     data = []

#     # 👑 ADMIN
#     if user["role"] == "admin":
#         data = await orders_collection.find().to_list(1000)

#     # 👤 SUPPLIER
#     elif user["role"] == "supplier":
#         all_orders = await orders_collection.find().to_list(1000)

#         for o in all_orders:
#             filtered_items = [
#                 i for i in o["items"]
#                 if i["supplier_email"] == user["email"]
#             ]

#             if filtered_items:
#                 o["items"] = filtered_items
#                 data.append(o)

#     # 👀 VIEWER
#     else:
#         data = await orders_collection.find({
#             "user_email": user["email"]
#         }).to_list(1000)

#     clean = []

#     # clean ids
#     for d in data:
#         d["id"] = str(d["_id"])
#         d.pop("_id", None)
#         clean.append(d)


#     return {"data": clean}