from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from app.schemas.product import ProductCreate
from app.services.product_service import ProductService
from app.utils.dependencies import get_current_user
from typing import List
import os
import uuid
import json

router = APIRouter(prefix="/products", tags=["Products"])

UPLOAD_DIR = "uploads/products"
VARIANT_UPLOAD_DIR = "uploads/variants"


def verify_supplier_role(user):
    if user.get("role") != "supplier":
        raise HTTPException(
            status_code=403,
            detail="Access denied. Only users with the 'supplier' role can perform this action.",
        )


async def save_upload_file(file: UploadFile, directory: str) -> str:
    os.makedirs(directory, exist_ok=True)
    filename = f"{uuid.uuid4()}_{file.filename}"
    filepath = os.path.join(directory, filename)
    with open(filepath, "wb") as buffer:
        buffer.write(await file.read())
    return f"/{directory}/{filename}"


@router.post("/json")
async def create_product_json(product: ProductCreate, user=Depends(get_current_user)):
    verify_supplier_role(user)
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
    variants: str = Form("[]"),
    image: UploadFile = File(None),
    variant_images: List[UploadFile] = File(None),
    user=Depends(get_current_user),
):
    verify_supplier_role(user)

    try:
        parsed_variants = json.loads(variants)
    except json.JSONDecodeError:
        raise HTTPException(status_code=422, detail="Invalid JSON format for variants")

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
        "variants": parsed_variants,
    }

    if image:
        data["image"] = await save_upload_file(image, UPLOAD_DIR)

    if variant_images:
        for idx, v_file in enumerate(variant_images):
            if idx < len(data["variants"]):
                content = await v_file.read()
                if content:
                    await v_file.seek(0)
                    path = await save_upload_file(v_file, VARIANT_UPLOAD_DIR)
                    data["variants"][idx]["image"] = path

    return await ProductService.create_product(data, user)


@router.put("/{product_id}")
async def update_product(
    product_id: str,
    name: str = Form(...),
    description: str = Form(None),
    category: str = Form(...),
    brand: str = Form(None),
    cost_price: float = Form(0),
    selling_price: float = Form(...),
    reorder_level: int = Form(0),
    tax: float = Form(0),
    unit: str = Form("piece"),
    variants: str = Form("[]"),
    image: UploadFile = File(None),
    variant_images: List[UploadFile] = File(None),
    user=Depends(get_current_user),
):
    verify_supplier_role(user)

    try:
        parsed_variants = json.loads(variants)
    except json.JSONDecodeError:
        raise HTTPException(status_code=422, detail="Invalid JSON format for variants")

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
        "variants": parsed_variants,
    }

    if image:
        if hasattr(image, "filename"):
            data["image"] = await save_upload_file(image, UPLOAD_DIR)

    if variant_images:
        for idx, v_file in enumerate(variant_images):
            if idx < len(data["variants"]):
                content = await v_file.read()
                if content:
                    await v_file.seek(0)
                    path = await save_upload_file(v_file, VARIANT_UPLOAD_DIR)
                    data["variants"][idx]["image"] = path

    return await ProductService.update_product(product_id, data)


@router.get("/")
async def get_products(user=Depends(get_current_user)):

    return await ProductService.get_products(user)


@router.delete("/{product_id}")
async def delete_product(product_id: str, user=Depends(get_current_user)):
    verify_supplier_role(user)
    return await ProductService.delete_product(product_id)
