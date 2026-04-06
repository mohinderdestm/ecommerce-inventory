from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from app.schemas.product import ProductCreate
from app.services.product_service import ProductService
from app.utils.dependencies import get_current_user

import os
import uuid

router = APIRouter(prefix="/products", tags=["Products"])

UPLOAD_DIR = "uploads/products"


@router.post("/json")
async def create_product_json(product: ProductCreate, user=Depends(get_current_user)):
    if user["role"] not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    return await ProductService.create_product(product.dict(), user)


@router.post("/")
async def create_product(
    name: str = Form(...),
    description: str = Form(None),
    category: str = Form(...),
    brand: str = Form(None),
    cost_price: float = Form(...),
    selling_price: float = Form(...),
    reorder_level: int = Form(0),
    tax: float = Form(0),
    unit: str = Form("piece"),
    image: UploadFile = File(None),
    user=Depends(get_current_user),
):
    if user["role"] not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    data = {
        "name": name,
        "description": description,
        "category": category,
        "brand": brand,
        "cost_price": cost_price,
        "selling_price": selling_price,
        "reorder_level": reorder_level,
        "tax": tax,
        "unit": unit,
    }

    if image:
        os.makedirs(UPLOAD_DIR, exist_ok=True)

        filename = f"{uuid.uuid4()}_{image.filename}"
        filepath = os.path.join(UPLOAD_DIR, filename)

        with open(filepath, "wb") as buffer:
            buffer.write(await image.read())

        data["image"] = f"/uploads/products/{filename}"

    return await ProductService.create_product(data, user)


@router.get("/")
async def get_products(user=Depends(get_current_user)):
    return await ProductService.get_products()


@router.put("/{product_id}")
async def update_product(product_id: str, data: dict, user=Depends(get_current_user)):
    if user["role"] not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    return await ProductService.update_product(product_id, data)


@router.delete("/{product_id}")
async def delete_product(product_id: str, user=Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admin can delete")

    return await ProductService.delete_product(product_id)
