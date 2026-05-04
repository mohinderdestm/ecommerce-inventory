from fastapi import (
    APIRouter,
    Depends,
    Form,
    UploadFile,
    File,
    HTTPException
)

from deps import get_current_user

from bson import ObjectId

import os

from database import (
    products_collection,
    audit_logs_collection
)

from datetime import datetime


router = APIRouter(
    prefix="/products",
    tags=["Products"]
)


@router.post("")
async def create_product(

    name: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),

    brand: str = Form(...),

    unit: str = Form(...),

    cost_price: float = Form(...),
    selling_price: float = Form(...),

    supplier_name: str = Form(None),
    supplier_email: str = Form(None),

    image: UploadFile = File(None),

    user=Depends(get_current_user)

):

    if user["role"] == "supplier":

        supplier_email = user["email"]

        supplier_name = (
            user.get("name")
            or "Unknown Supplier"
        )

    elif user["role"] == "admin":

        if not supplier_email:

            raise HTTPException(
                status_code=400,
                detail="Supplier required"
            )

        if not supplier_name:

            raise HTTPException(
                status_code=400,
                detail="Supplier name required"
            )

    else:

        raise HTTPException(
            status_code=403,
            detail="Not allowed"
        )

    image_url = ""

    if image:

        os.makedirs(
            "uploads",
            exist_ok=True
        )

        path = f"uploads/{image.filename}"

        with open(path, "wb") as f:

            f.write(
                await image.read()
            )

        image_url = path

    product = {

        "name": name,

        "description": description,

        "category": category,

        "brand": brand,

        "unit": unit,

        "cost_price": float(cost_price),

        "selling_price": float(
            selling_price
        ),

        "image": image_url,

        "supplier_name": supplier_name,

        "supplier_email": supplier_email,

        "variants": []

    }

    result = await products_collection.insert_one(
        product
    )


    try:

        username = (
            user.get("name")
            or user.get("email")
            or "Unknown User"
        )

        log_data = {

            "action": "PRODUCT_CREATED",

            "message": (
                f"{username} created "
                f"product ({name})"
            ),

            "user_name": username,

            "user_email": user.get(
                "email"
            ),

            "role": user.get(
                "role",
                "-"
            ),

            "entity": "product",

            "entity_id": str(
                result.inserted_id
            ),

            "timestamp": datetime.utcnow()

        }

        await audit_logs_collection.insert_one(
            log_data
        )

        print("CREATE LOG INSERTED")

    except Exception as e:

        print(
            "AUDIT LOG ERROR:",
            str(e)
        )

    product["id"] = str(
        result.inserted_id
    )

    return {
        "data": product
    }


@router.get("")
async def get_products(
    user=Depends(get_current_user)
):

    if user["role"] == "admin":

        data = (
            await products_collection.find()
            .to_list(1000)
        )

    elif user["role"] == "supplier":

        data = (
            await products_collection.find({

                "supplier_email":
                user["email"]

            }).to_list(1000)
        )

    else:

        data = (
            await products_collection.find()
            .to_list(1000)
        )

    clean = []

    for d in data:

        d["id"] = str(d["_id"])

        d.pop("_id", None)

        variants = []

        for v in d.get(
            "variants",
            []
        ):

            new_v = v.copy()

            if user["role"] == "viewer":

                stock = v.get(
                    "stock",
                    0
                )

                if stock == 0:

                    new_v[
                        "availability"
                    ] = "Out of Stock"

                elif stock <= 5:

                    new_v[
                        "availability"
                    ] = "Few left"

                else:

                    new_v[
                        "availability"
                    ] = "In Stock"

                new_v[
                    "has_stock"
                ] = stock > 0

            variants.append(new_v)

        d["variants"] = variants

        clean.append(d)

    return {
        "data": clean
    }



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

    product = (
        await products_collection.find_one({

            "_id": ObjectId(id)

        })
    )

    if not product:

        raise HTTPException(
            status_code=404
        )

    if user["role"] == "admin":

        pass

    elif user["role"] == "supplier":

        if (
            product[
                "supplier_email"
            ]
            != user["email"]
        ):

            raise HTTPException(
                status_code=403,
                detail="Not your product"
            )

    else:

        raise HTTPException(
            status_code=403
        )

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

        os.makedirs(
            "uploads",
            exist_ok=True
        )

        path = (
            f"uploads/{image.filename}"
        )

        with open(path, "wb") as f:

            f.write(
                await image.read()
            )

        update_data["image"] = path

    await products_collection.update_one(

        {"_id": ObjectId(id)},

        {
            "$set": update_data
        }

    )


    try:

        updated_product = await products_collection.find_one({
            "_id": ObjectId(id)
        })

        username = (
            user.get("name")
            or user.get("email")
            or "Unknown User"
        )

        log_data = {

            "action": "PRODUCT_UPDATED",

            "message": (
                f"{username} updated product "
                f"({updated_product.get('name')})"
            ),

            "user_name": username,

            "user_email": user.get("email"),

            "role": user.get("role", "-"),

            "entity": "product",

            "entity_id": id,

            "timestamp": datetime.utcnow()

        }

        await audit_logs_collection.insert_one(
            log_data
        )

        print("UPDATE LOG INSERTED")

    except Exception as e:

        print("UPDATE LOG ERROR:", str(e))

    return {
        "message": "Updated"
    }


@router.delete("/{id}")
async def delete_product(

    id: str,

    user=Depends(get_current_user)

):

    product = (
        await products_collection.find_one({

            "_id": ObjectId(id)

        })
    )

    if not product:

        raise HTTPException(
            status_code=404
        )

    if user["role"] == "admin":

        pass

    elif user["role"] == "supplier":

        if (
            product[
                "supplier_email"
            ]
            != user["email"]
        ):

            raise HTTPException(
                status_code=403,
                detail="Not your product"
            )

    else:

        raise HTTPException(
            status_code=403
        )

    await products_collection.delete_one({

        "_id": ObjectId(id)

    })


    try:

        username = (
            user.get("name")
            or user.get("email")
            or "Unknown User"
        )

        log_data = {

            "action": "PRODUCT_DELETED",

            "message": (
                f"{username} deleted product "
                f"{product.get('name')}"
            ),

            "user_name": username,

            "user_email": user.get("email"),

            "role": user.get("role", "-"),

            "entity": "product",

            "entity_id": id,

            "timestamp": datetime.utcnow()

        }

        await audit_logs_collection.insert_one(
            log_data
        )

        print("DELETE LOG INSERTED")

    except Exception as e:

        print("DELETE LOG ERROR:", str(e))

    return {
        "message": "Deleted"
    }

