from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from datetime import datetime
from database import notifications_collection, users_collection
from services.notification_services import create_notification

from database import (
    cart_collection,
    products_collection,
    orders_collection
)
from services.email_services import send_email_simulation
from deps import get_current_user

router = APIRouter(tags=["Cart"])


@router.post("/cart/add")
async def add_to_cart(data: dict, user=Depends(get_current_user)):

    if user["role"] != "viewer":
        raise HTTPException(status_code=403)

    product = await products_collection.find_one({
        "_id": ObjectId(data["product_id"])
    })

    if not product:
        raise HTTPException(status_code=404)

    variant = None

    for v in product.get("variants", []):
        if v["id"] == data["variant_id"]:
            variant = v
            break

    if not variant:
        raise HTTPException(status_code=404)

    if variant["stock"] < data["quantity"]:
        raise HTTPException(
            status_code=400,
            detail="Insufficient stock"
        )

    cart = await cart_collection.find_one({
        "user_email": user["email"]
    })

    if not cart:

        cart = {
            "user_email": user["email"],
            "items": [],
            "updated_at": datetime.utcnow().isoformat()
        }

    found = False

    for item in cart["items"]:

        if item["variant_id"] == data["variant_id"]:
            item["quantity"] += data["quantity"]
            found = True
            break

    if not found:

        cart["items"].append({
            "product_id": data["product_id"],
            "variant_id": data["variant_id"],
            "quantity": data["quantity"]
        })

    await cart_collection.update_one(
        {"user_email": user["email"]},
        {"$set": cart},
        upsert=True
    )

    return {"message": "Added to cart"}



@router.get("/cart")
async def get_my_cart(user=Depends(get_current_user)):

    if user["role"] != "viewer":
        raise HTTPException(status_code=403)

    cart = await cart_collection.find_one({
        "user_email": user["email"]
    })

    if not cart:
        return {
            "items": [],
            "total": 0
        }

    enriched = []
    total = 0

    for item in cart["items"]:

        product = await products_collection.find_one({
            "_id": ObjectId(item["product_id"])
        })

        if not product:
            continue

        for v in product.get("variants", []):

            if v["id"] == item["variant_id"]:

                subtotal = (
                    v["price"] * item["quantity"]
                )

                total += subtotal

                enriched.append({
                    "product_id": item["product_id"],
                    "variant_id": v["id"],
                    "name": product["name"],
                    "image": (
                        v.get("image")
                        or product.get("image")
                    ),
                    "color": v["color"],
                    "size": v["size"],
                    "sku": v["sku"],
                    "price": v["price"],
                    "quantity": item["quantity"],
                    "subtotal": subtotal
                })

    return {
        "items": enriched,
        "total": total
    }

@router.post("/cart/checkout")
async def checkout(user=Depends(get_current_user)):

    if user["role"] != "viewer":
        raise HTTPException(status_code=403)

    cart = await cart_collection.find_one({
        "user_email": user["email"]
    })

    if not cart or not cart["items"]:
        raise HTTPException(
            status_code=400,
            detail="Cart empty"
        )

    order_items = []
    total = 0

    for item in cart["items"]:

        product = await products_collection.find_one({
            "_id": ObjectId(item["product_id"])
        })

        if not product:
            continue

        variant = None

        for v in product["variants"]:

            if v["id"] == item["variant_id"]:
                variant = v
                break

        if not variant:
            continue

        if variant["stock"] < item["quantity"]:

            raise HTTPException(
                status_code=400,
                detail=f"{product['name']} out of stock"
            )

        variant["stock"] -= item["quantity"]

        if variant["stock"] <= 5:

            admins = await users_collection.find({
                "role": "admin"
            }).to_list(100)

            for admin in admins:

                await create_notification(
                    admin["email"],
                    "Low Stock Alert",
                    f"{product['name']} ({variant['sku']}) stock is low: {variant['stock']} left",
                    "inventory"
                )
                await send_email_simulation(
                    admin["email"],
                    "Low Stock Alert",
                    f"{product['name']} ({variant['sku']}) stock is low: {variant['stock']} left",
                    "inventory"
                )

        subtotal = (
            variant["price"] * item["quantity"]
        )

        total += subtotal

        order_items.append({

            "product_id": item["product_id"],
            "variant_id": variant["id"],
            "product_name": product["name"],
            "supplier_email": product["supplier_email"],

            "color": variant["color"],
            "size": variant["size"],
            "sku": variant["sku"],

            "price": variant["price"],
            "quantity": item["quantity"],

            "image": (
                variant.get("image")
                or product.get("image")
            )

        })

        await products_collection.update_one(
            {"_id": ObjectId(item["product_id"])},
            {
                "$set": {
                    "variants": product["variants"]
                }
            }
        )

    order = {

        "user_email": user["email"],
        "status": "Confirmed",

        "items": order_items,

        "total": total,

        "created_at": datetime.utcnow().isoformat()

    }

    result = await orders_collection.insert_one(
        order
    )
    await send_email_simulation(
    user["email"],
    "Order Confirmation",
    f"Your order #{str(result.inserted_id)[-6:]} has been placed successfully.",
    "order"
    )

    admins = await users_collection.find({
        "role": "admin"
    }).to_list(100)

    for admin in admins:

        await create_notification(
            admin["email"],
            "New Order Placed",
            f"{user['email']} placed a new order.",
            "order"
        )
        await send_email_simulation(
        admin["email"],
        "New Order Alert",
        f"{user['email']} placed a new order.",
        "order"
    )

    await create_notification(
        user["email"],
        "Order Confirmed",
        f"Your order #{str(result.inserted_id)[-6:]} has been placed successfully.",
        "order"
    )


    await cart_collection.delete_one({
        "user_email": user["email"]
    })

    return {

        "message": "Order placed",

        "order_id": str(
            result.inserted_id
        )

    }

@router.get("/cart/all")
async def get_all_carts(user=Depends(get_current_user)):

    if user["role"] != "admin":
        raise HTTPException(status_code=403)

    carts = await cart_collection.find().to_list(100)

    clean = []

    for c in carts:

        clean.append({
            "id": str(c["_id"]),
            "user_email": c["user_email"],
            "items": c.get("items", []),
            "updated_at": c.get("updated_at")
        })

    return {
        "data": clean
    }

@router.put("/cart/update")
async def update_cart_quantity(
    data: dict,
    user=Depends(get_current_user)
):

    if user["role"] != "viewer":
        raise HTTPException(status_code=403)

    cart = await cart_collection.find_one({
        "user_email": user["email"]
    })

    if not cart:
        raise HTTPException(
            status_code=404,
            detail="Cart not found"
        )

    for item in cart["items"]:

        if item["variant_id"] == data["variant_id"]:

            if data["quantity"] <= 0:

                cart["items"].remove(item)

            else:

                product = await products_collection.find_one({
                    "_id": ObjectId(item["product_id"])
                })

                variant = None

                for v in product["variants"]:

                    if v["id"] == item["variant_id"]:
                        variant = v
                        break

                if not variant:
                    raise HTTPException(
                        status_code=404,
                        detail="Variant not found"
                    )

                if data["quantity"] > variant["stock"]:

                    raise HTTPException(
                        status_code=400,
                        detail="Not enough stock"
                    )

                item["quantity"] = data["quantity"]

            break

    await cart_collection.update_one(
        {"user_email": user["email"]},
        {
            "$set": {
                "items": cart["items"]
            }
        }
    )

    return {
        "message": "Cart updated"
    }