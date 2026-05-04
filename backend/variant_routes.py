# variant_routes.py

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form
)

from bson import ObjectId

from deps import get_current_user

from database import (
    products_collection,
    audit_logs_collection
)

from datetime import datetime

import os
import random


router = APIRouter(
    prefix="/variants",
    tags=["Variants"]
)



@router.post("/{product_id}")
async def add_variant(

    product_id: str,

    color: str = Form(...),

    size: str = Form(...),

    price: float = Form(...),

    stock: int = Form(...),

    image: UploadFile = File(None),

    user=Depends(get_current_user)

):

    product = await products_collection.find_one({
        "_id": ObjectId(product_id)
    })

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    if user["role"] == "supplier":

        if product["supplier_email"] != user["email"]:
            raise HTTPException(status_code=403)

    elif user["role"] != "admin":

        raise HTTPException(status_code=403)

    sku = f"SKU-{random.randint(10000,99999)}"

    image_url = ""

    if image:

        os.makedirs("uploads", exist_ok=True)

        path = f"uploads/{image.filename}"

        with open(path, "wb") as f:
            f.write(await image.read())

        image_url = path

    variant = {

        "id": str(ObjectId()),

        "color": color,

        "size": size,

        "price": price,

        "stock": stock,

        "sku": sku,

        "image": image_url

    }

    await products_collection.update_one(

        {"_id": ObjectId(product_id)},

        {"$push": {"variants": variant}}

    )


    try:

        username = (
            user.get("name")
            or user.get("email")
            or "Unknown User"
        )

        log_data = {

            "action": "VARIANT_CREATED",

            "message": (
                f"{username} added variant "
                f"{color}/{size} to "
                f"{product.get('name')}"
            ),

            "user_name": username,

            "user_email": user.get("email"),

            "role": user.get("role", "-"),

            "entity": "variant",

            "entity_id": variant["id"],

            "timestamp": datetime.utcnow()

        }

        await audit_logs_collection.insert_one(
            log_data
        )

    except Exception as e:

        print("VARIANT CREATE LOG ERROR:", str(e))

    return {
        "data": variant
    }



@router.get("/{product_id}")
async def get_variants(

    product_id: str,

    user=Depends(get_current_user)

):

    product = await products_collection.find_one({
        "_id": ObjectId(product_id)
    })

    if not product:
        raise HTTPException(status_code=404)

    if user["role"] == "supplier":

        if product["supplier_email"] != user["email"]:
            raise HTTPException(status_code=403)

    elif user["role"] not in ["admin", "viewer"]:

        raise HTTPException(status_code=403)

    return {
        "data": product.get("variants", [])
    }



@router.put("/{product_id}/{variant_id}")
async def update_variant(

    product_id: str,

    variant_id: str,

    color: str = Form(...),

    size: str = Form(...),

    price: float = Form(...),

    stock: int = Form(...),

    user=Depends(get_current_user)

):

    product = await products_collection.find_one({
        "_id": ObjectId(product_id)
    })

    if not product:
        raise HTTPException(status_code=404)

    if user["role"] == "admin":

        pass

    elif user["role"] == "supplier":

        if product["supplier_email"] != user["email"]:

            raise HTTPException(
                status_code=403,
                detail="Not your product"
            )

    else:

        raise HTTPException(status_code=403)

    variants = product.get("variants", [])

    old_stock = 0

    for v in variants:

        if v["id"] == variant_id:

            old_stock = v.get("stock", 0)

            v["color"] = color
            v["size"] = size
            v["price"] = price
            v["stock"] = stock

    await products_collection.update_one(

        {"_id": ObjectId(product_id)},

        {"$set": {"variants": variants}}

    )


    try:

        username = (
            user.get("name")
            or user.get("email")
            or "Unknown User"
        )

        stock_change = (
            f"Stock changed "
            f"from {old_stock} to {stock}"
        )

        log_data = {

            "action": "VARIANT_UPDATED",

            "message": (
                f"{username} updated variant "
                f"{color}/{size} of "
                f"{product.get('name')} "
                f"({stock_change})"
            ),

            "user_name": username,

            "user_email": user.get("email"),

            "role": user.get("role", "-"),

            "entity": "variant",

            "entity_id": variant_id,

            "timestamp": datetime.utcnow()

        }

        await audit_logs_collection.insert_one(
            log_data
        )

    except Exception as e:

        print("VARIANT UPDATE LOG ERROR:", str(e))

    return {
        "message": "Variant updated"
    }



@router.delete("/{product_id}/{variant_id}")
async def delete_variant(

    product_id: str,

    variant_id: str,

    user=Depends(get_current_user)

):

    product = await products_collection.find_one({
        "_id": ObjectId(product_id)
    })

    if not product:
        raise HTTPException(status_code=404)

    if user["role"] == "admin":

        pass

    elif user["role"] == "supplier":

        if product["supplier_email"] != user["email"]:

            raise HTTPException(
                status_code=403,
                detail="Not your product"
            )

    else:

        raise HTTPException(status_code=403)

    deleted_variant = None

    for v in product.get("variants", []):

        if v["id"] == variant_id:
            deleted_variant = v
            break

    await products_collection.update_one(

        {"_id": ObjectId(product_id)},

        {"$pull": {"variants": {"id": variant_id}}}

    )

    

    try:

        username = (
            user.get("name")
            or user.get("email")
            or "Unknown User"
        )

        variant_name = "Unknown Variant"

        if deleted_variant:

            variant_name = (
                f"{deleted_variant.get('color')}/"
                f"{deleted_variant.get('size')}"
            )

        log_data = {

            "action": "VARIANT_DELETED",

            "message": (
                f"{username} deleted variant "
                f"{variant_name} from "
                f"{product.get('name')}"
            ),

            "user_name": username,

            "user_email": user.get("email"),

            "role": user.get("role", "-"),

            "entity": "variant",

            "entity_id": variant_id,

            "timestamp": datetime.utcnow()

        }

        await audit_logs_collection.insert_one(
            log_data
        )

    except Exception as e:

        print("VARIANT DELETE LOG ERROR:", str(e))

    return {
        "message": "Variant deleted"
    }

