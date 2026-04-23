from fastapi import APIRouter, Depends, Form, UploadFile, File, HTTPException
from deps import get_current_user
# from database import products
from bson import ObjectId
import os
from database import products_collection,orders_collection

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("")
async def create_product(
    name: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    brand: str = Form(...),
    unit: str = Form(...),
    cost_price: float = Form(...),
    selling_price: float = Form(...),
    supplier_email: str = Form(None),
    image: UploadFile = File(None),
    user=Depends(get_current_user)
):

    if user["role"] == "supplier":
        supplier_email = user["email"]

    elif user["role"] == "admin":
        if not supplier_email or supplier_email == "":
            raise HTTPException(status_code=400, detail="Supplier required")

    else:
        raise HTTPException(status_code=403, detail="Not allowed")

    # ✅ IMAGE
    image_url = ""
    if image:
        os.makedirs("uploads", exist_ok=True)
        path = f"uploads/{image.filename}"

        with open(path, "wb") as f:
            f.write(await image.read())

        image_url = path

    # ✅ PRODUCT
    product = {
        "name": name,
        "description": description,
        "category": category,
        "brand": brand,
        "unit": unit,
        "cost_price": float(cost_price),
        "selling_price": float(selling_price),
        "image": image_url,
        "supplier_email": supplier_email,
        "variants": []
    }

    result = await products_collection.insert_one(product)

    product["id"] = str(result.inserted_id)
    return {"data": product}


# ✅ GET PRODUCTS (ROLE BASED)
@router.get("")
async def get_products(user=Depends(get_current_user)):
    if user["role"] == "admin":
        data = await products_collection.find().to_list(1000)

    elif user["role"] == "supplier":
        data = await products_collection.find({
            "supplier_email": user["email"]
        }).to_list(1000)

    else: 
        data = await products_collection.find().to_list(1000)

    clean = []

    for d in data:
        d["id"] = str(d["_id"])
        d.pop("_id", None)

        variants = []

        for v in d.get("variants", []):
            new_v = v.copy()

            if user["role"] == "viewer":
            
                new_v.pop("stock", None)

                if v.get("stock", 0) == 0:
                    new_v["availability"] = "Out of Stock"
                elif v.get("stock", 0) <= 5:
                    new_v["availability"] = "Few left"
                else:
                    new_v["availability"] = "In Stock"

            variants.append(new_v)

        d["variants"] = variants
        clean.append(d)

    return {"data": clean}


# ✅ DELETE PRODUCT (ADMIN ONLY)
@router.delete("/{id}")
async def delete_product(id: str, user=Depends(get_current_user)):
    product = await products_collection.find_one({"_id": ObjectId(id)})

    if not product:
        raise HTTPException(status_code=404)

    if user["role"] == "admin":
        pass

    # ✅ SUPPLIER → only own product
    elif user["role"] == "supplier":
        if product["supplier_email"] != user["email"]:
            raise HTTPException(status_code=403, detail="Not your product")

    else:
        raise HTTPException(status_code=403)

    await products_collection.delete_one({"_id": ObjectId(id)})

    return {"message": "Deleted"}


# ✅ UPDATE PRODUCT
@router.put("/{id}")
async def update_product(
    id: str,
    name: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    brand: str = Form(...),
    unit: str = Form(...),
    cost_price: float = Form(...),
    selling_price: float = Form(...),
    image: UploadFile = File(None),
    user=Depends(get_current_user)
):
    product = await products_collection.find_one({"_id": ObjectId(id)})

    if not product:
        raise HTTPException(status_code=404)

 
    if user["role"] == "admin":
        pass

    elif user["role"] == "supplier":
        if product["supplier_email"] != user["email"]:
            raise HTTPException(status_code=403, detail="Not your product")

    else:
        raise HTTPException(status_code=403)

    update_data = {
        "name": name,
        "description": description,
        "category": category,
        "brand": brand,
        "unit": unit,
        "cost_price": cost_price,
        "selling_price": selling_price
    }

    if image:
        os.makedirs("uploads", exist_ok=True)
        path = f"uploads/{image.filename}"

        with open(path, "wb") as f:
            f.write(await image.read())

        update_data["image"] = path

    await products_collection.update_one(
        {"_id": ObjectId(id)},
        {"$set": update_data}
    )

    return {"message": "Updated"}


