from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from datetime import datetime

from database import (
    cart_collection,
    products_collection,
    orders_collection
)

from deps import get_current_user

router = APIRouter(tags=["Cart"])


# ================= ADD TO CART =================

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


# ================= GET MY CART =================

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


# ================= CHECKOUT =================

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
            "quantity": item["quantity"]
        })

        await products_collection.update_one(
            {"_id": ObjectId(item["product_id"])},
            {"$set": {"variants": product["variants"]}}
        )

    order = {
        "user_email": user["email"],
        "status": "Confirmed",
        "items": order_items,
        "total": total,
        "created_at": datetime.utcnow().isoformat()
    }

    result = await orders_collection.insert_one(order)

    await cart_collection.delete_one({
        "user_email": user["email"]
    })

    return {
        "message": "Order placed",
        "order_id": str(result.inserted_id)
    }


# ================= ADMIN SEE ALL CARTS =================

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