from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from deps import get_current_user
from database import products_collection

router = APIRouter(prefix="/variants", tags=["Variants"])


from fastapi import UploadFile, File, Form
import os
import random

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
    product = await products_collection.find_one({"_id": ObjectId(product_id)})

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

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

    return {"data": variant}


@router.get("/{product_id}")
async def get_variants(product_id: str, user=Depends(get_current_user)):
    product = await products_collection.find_one({"_id": ObjectId(product_id)})

    if not product:
        raise HTTPException(status_code=404)


    if user["role"] == "supplier":
        if product["supplier_email"] != user["email"]:
            raise HTTPException(status_code=403)

    elif user["role"] not in ["admin", "viewer"]:
        raise HTTPException(status_code=403)

    return {"data": product.get("variants", [])}

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
    product = await products_collection.find_one({"_id": ObjectId(product_id)})

    if not product:
        raise HTTPException(status_code=404)


    if user["role"] == "admin":
        pass
    elif user["role"] == "supplier":
        if product["supplier_email"] != user["email"]:
            raise HTTPException(status_code=403, detail="Not your product")
    else:
        raise HTTPException(status_code=403)

    variants = product.get("variants", [])

    for v in variants:
        if v["id"] == variant_id:
            v["color"] = color
            v["size"] = size
            v["price"] = price
            v["stock"] = stock

    await products_collection.update_one(
        {"_id": ObjectId(product_id)},
        {"$set": {"variants": variants}}
    )

    return {"message": "Variant updated"}


@router.delete("/{product_id}/{variant_id}")
async def delete_variant(product_id: str, variant_id: str, user=Depends(get_current_user)):
    product = await products_collection.find_one({"_id": ObjectId(product_id)})

    if not product:
        raise HTTPException(status_code=404)

    if user["role"] == "admin":
        pass
    elif user["role"] == "supplier":
        if product["supplier_email"] != user["email"]:
            raise HTTPException(status_code=403, detail="Not your product")
    else:
        raise HTTPException(status_code=403)

    await products_collection.update_one(
        {"_id": ObjectId(product_id)},
        {"$pull": {"variants": {"id": variant_id}}}
    )

    return {"message": "Variant deleted"}