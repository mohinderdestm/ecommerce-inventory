from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId

from database import (
    products_collection,
    orders_collection,
    warehouse_collection,
     audit_logs_collection
)

from deps import get_current_user

from services.notification_services import (
    create_notification
)

import datetime

router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)

VALID_STATUS = [
    "Draft",
    "Confirmed",
    "Packed",
    "Shipped",
    "Delivered",
    "Cancelled",
    "Returned"
]


def serialize_order(d):

    return {
        "id": str(d["_id"]),
        "user_email": d.get("user_email"),
        "status": d.get("status"),
        "items": d.get("items", []),
        "total": d.get("total", 0),
        "warehouse_id": d.get("warehouse_id"),
        "warehouse_name": d.get("warehouse_name"),
        "created_at": d.get("created_at")
    }


@router.post("")
async def create_order(
    user=Depends(get_current_user)
):

    order = {
        "user_email": user["email"],
        "status": "Draft",
        "items": [],
        "total": 0,
        "warehouse_id": None,
        "warehouse_name": None,
        "created_at": datetime.datetime.utcnow().isoformat()
    }

    res = await orders_collection.insert_one(
        order
    )

    return {
        "data": {
            "id": str(res.inserted_id),
            "user_email": order["user_email"],
            "status": order["status"],
            "items": [],
            "total": 0,
            "warehouse_id": None,
            "warehouse_name": None,
            "created_at": order["created_at"]
        }
    }


@router.put("/{order_id}/warehouse")
async def assign_warehouse(
    order_id: str,
    data: dict,
    user=Depends(get_current_user)
):

    if user["role"] != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only admin can assign warehouse"
        )

    warehouse = await warehouse_collection.find_one({
        "_id": ObjectId(data["warehouse_id"])
    })

    if not warehouse:
        raise HTTPException(
            status_code=404,
            detail="Warehouse not found"
        )

    await orders_collection.update_one(
        {"_id": ObjectId(order_id)},
        {
            "$set": {
                "warehouse_id": data["warehouse_id"],
                "warehouse_name": warehouse["name"]
            }
        }
    )

    return {
        "message": "Warehouse assigned"
    }


@router.post("/{order_id}/add")
async def add_item(
    order_id: str,
    data: dict,
    user=Depends(get_current_user)
):

    order = await orders_collection.find_one({
        "_id": ObjectId(order_id)
    })

    if not order:
        raise HTTPException(status_code=404)

    if order["status"] != "Draft":
        raise HTTPException(
            status_code=400,
            detail="Not editable"
        )

    if not data.get("variant_id"):
        raise HTTPException(
            status_code=400,
            detail="Variant required"
        )

    product = await products_collection.find_one({
        "_id": ObjectId(data["product_id"])
    })

    variant = next(
        (
            v for v in product["variants"]
            if v["id"] == data["variant_id"]
        ),
        None
    )

    if not variant:
        raise HTTPException(status_code=404)

    if variant["stock"] < data["quantity"]:
        raise HTTPException(
            status_code=400,
            detail="Insufficient stock"
        )

    item = {
        "product_id": data["product_id"],
        "variant_id": data["variant_id"],
        "product_name": product["name"],
        "supplier_email": product["supplier_email"],
        "color": variant["color"],
        "size": variant["size"],
        "sku": variant["sku"],
        "price": variant["price"],
        "quantity": data["quantity"],
        "image": variant.get("image")
    }

    new_total = order["total"] + (
        variant["price"] * data["quantity"]
    )

    await orders_collection.update_one(
        {"_id": ObjectId(order_id)},
        {
            "$push": {"items": item},
            "$set": {"total": new_total}
        }
    )

    return {
        "message": "Item added"
    }


@router.post("/{order_id}/confirm")
async def confirm_order(
    order_id: str,
    user=Depends(get_current_user)
):

    order = await orders_collection.find_one({
        "_id": ObjectId(order_id)
    })

    if not order:
        raise HTTPException(status_code=404)

    if order["status"] != "Draft":
        raise HTTPException(status_code=400)

    if not order.get("warehouse_id"):
        raise HTTPException(
            status_code=400,
            detail="Please assign warehouse first"
        )

    for item in order["items"]:

        product = await products_collection.find_one({
            "_id": ObjectId(item["product_id"])
        })

        for v in product["variants"]:

            if v["id"] == item["variant_id"]:

                if v["stock"] < item["quantity"]:
                    raise HTTPException(
                        status_code=400,
                        detail="Stock changed"
                    )

                v["stock"] -= item["quantity"]

        await products_collection.update_one(
            {"_id": ObjectId(item["product_id"])},
            {
                "$set": {
                    "variants": product["variants"]
                }
            }
        )

    await orders_collection.update_one(
        {"_id": ObjectId(order_id)},
        {
            "$set": {
                "status": "Confirmed"
            }
        }
    )

    await create_notification(
        order["user_email"],
        "Order Confirmed",
        f"Your order #{str(order['_id'])[-6:]} has been confirmed",
        "order"
    )

    return {
        "message": "Confirmed"
    }


@router.put("/{order_id}/status")
async def update_status(
    order_id: str,
    data: dict,
    user=Depends(get_current_user)
):

    if data["status"] not in VALID_STATUS:
        raise HTTPException(status_code=400)

    if user["role"] == "admin":
        pass

    elif user["role"] == "supplier":

        if data["status"] not in [
            "Packed",
            "Shipped"
        ]:
            raise HTTPException(status_code=403)

    else:
        raise HTTPException(status_code=403)

    await orders_collection.update_one(
        {"_id": ObjectId(order_id)},
        {
            "$set": {
                "status": data["status"]
            }
        }
    )

    order = await orders_collection.find_one({
        "_id": ObjectId(order_id)
    })

    await create_notification(
        order["user_email"],
        "Order Status Updated",
        f"Your order #{str(order['_id'])[-6:]} is now {data['status']}",
        "order"
    )

    return {
        "message": "Updated"
    }


@router.post("/{order_id}/cancel")
async def cancel_order(

    order_id: str,

    user=Depends(get_current_user)

):

    order = await orders_collection.find_one({

        "_id": ObjectId(order_id)

    })

    if not order:
        raise HTTPException(status_code=404)

    if user["role"] == "viewer":

        if order["user_email"] != user["email"]:
            raise HTTPException(status_code=403)

        if order["status"] in [

            "Shipped",

            "Delivered",

            "Cancelled"

        ]:

            raise HTTPException(

                status_code=400,

                detail=(
                    "Order cannot "
                    "be cancelled"
                )

            )

    elif user["role"] == "supplier":

        raise HTTPException(status_code=403)

    for item in order["items"]:

        product = await products_collection.find_one({

            "_id": ObjectId(
                item["product_id"]
            )

        })

        for v in product["variants"]:

            if (
                v["id"]
                == item["variant_id"]
            ):

                v["stock"] += (
                    item["quantity"]
                )

        await products_collection.update_one(

            {
                "_id": ObjectId(
                    item["product_id"]
                )
            },

            {
                "$set": {
                    "variants":
                    product["variants"]
                }
            }

        )

    cancelled_by = (

        user.get("name")

        or user.get("email")

        or "Unknown User"

    )

    await orders_collection.update_one(

        {"_id": ObjectId(order_id)},

        {
            "$set": {

                "status": "Cancelled",

                "cancelled_by":
                cancelled_by,

                "cancelled_at":
                datetime.datetime.utcnow(),

                "cancelled_by_role":
                user.get("role", "-")

            }
        }

    )

    await create_notification(

        order["user_email"],

        "Order Cancelled",

        (
            f"Your order "
            f"#{str(order['_id'])[-6:]} "
            f"has been cancelled"
        ),

        "order"

    )


    try:

        log_data = {

            "action": "ORDER_CANCELLED",

            "message": (

                f"{cancelled_by} "

                f"cancelled order "

                f"#{str(order['_id'])[-6:]}"

            ),

            "user_name": cancelled_by,

            "user_email": user.get(
                "email"
            ),

            "role": user.get(
                "role",
                "-"
            ),

            "entity": "order",

            "entity_id": order_id,

            "timestamp":
            datetime.datetime.utcnow()

        }

        await audit_logs_collection.insert_one(
            log_data
        )

    except Exception as e:

        print(
            "ORDER CANCEL LOG ERROR:",
            str(e)
        )

    return {

        "message": "Cancelled"

    }

@router.get("")
async def get_orders(
    user=Depends(get_current_user)
):

    data = []

    if user["role"] == "admin":

        data = await orders_collection.find().to_list(1000)

    elif user["role"] == "supplier":

        all_orders = await orders_collection.find().to_list(1000)

        for o in all_orders:

            items = [
                i for i in o["items"]
                if i["supplier_email"] == user["email"]
            ]

            if items:
                o["items"] = items
                data.append(o)

    else:

        data = await orders_collection.find({
            "user_email": user["email"]
        }).to_list(1000)

    return {
        "data": [
            serialize_order(d)
            for d in data
        ]
    }

