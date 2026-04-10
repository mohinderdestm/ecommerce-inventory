from fastapi import APIRouter, Depends, UploadFile, File, Form, Query, HTTPException
from typing import Optional
from app.services.product_service import ProductService
from app.core.dependencies import get_current_user, require_roles
import shutil
import os
import uuid

router = APIRouter(prefix="/products", tags=["Products"])

UPLOAD_DIR = "static/uploads/products"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ==================== CREATE ====================

@router.post("/")
async def create_product(
    name: str = Form(...),
    description: str = Form(""),
    category_id: Optional[str] = Form(None),
    subcategory_id: Optional[str] = Form(None),
    brand: str = Form(""),
    supplier_ids: Optional[str] = Form(None),
    cost_price: float = Form(...),
    selling_price: float = Form(...),
    quantity: int = Form(0),
    reorder_level: int = Form(10),
    tax_percentage: float = Form(0),
    unit: str = Form("pcs"),
    tags: Optional[str] = Form(None),
    sku: Optional[str] = Form(None),
    file: UploadFile = File(...),
    user=Depends(require_roles(["admin", "supplier"]))  # Only admin & supplier
):
    # Handle file upload
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"{uuid.uuid4()}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    image_url = f"/static/uploads/products/{filename}"
    image_metadata = {
        "filename": file.filename,
        "size": file_size,
        "content_type": file.content_type
    }

    supplier_list = [s.strip() for s in supplier_ids.split(",") if s.strip()] if supplier_ids else []
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

    data = {
        "name": name,
        "description": description,
        "category_id": category_id if category_id else None,
        "subcategory_id": subcategory_id if subcategory_id else None,
        "brand": brand,
        "supplier_ids": supplier_list,
        "cost_price": cost_price,
        "selling_price": selling_price,
        "quantity": quantity,
        "reorder_level": reorder_level,
        "tax_percentage": tax_percentage,
        "unit": unit,
        "tags": tag_list,
        "sku": sku if sku else None
    }

    return await ProductService.create_product(data, image_url, image_metadata, user["user_id"])


# ==================== READ (All users can read) ====================

@router.get("/")
async def get_products(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    user=Depends(get_current_user)  # Any authenticated user
):
    return await ProductService.get_all_products(page, limit)


@router.get("/search")
async def search_products(
    search: Optional[str] = Query(None),
    category_id: Optional[str] = Query(None),
    subcategory_id: Optional[str] = Query(None),
    brand: Optional[str] = Query(None),
    supplier_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    in_stock: Optional[bool] = Query(None),
    low_stock: Optional[bool] = Query(None),
    tags: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    user=Depends(get_current_user)  # Any authenticated user
):
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else None

    return await ProductService.search_products(
        search=search,
        category_id=category_id,
        subcategory_id=subcategory_id,
        brand=brand,
        supplier_id=supplier_id,
        status=status,
        min_price=min_price,
        max_price=max_price,
        in_stock=in_stock,
        low_stock=low_stock,
        tags=tag_list,
        page=page,
        limit=limit
    )


@router.get("/low-stock")
async def get_low_stock_products(
    user=Depends(require_roles(["admin", "supplier"]))  #  Only admin & supplier
):
    return await ProductService.get_low_stock_products()


@router.get("/my-products")
async def get_my_products(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    user=Depends(require_roles(["admin", "supplier"]))  #  Supplier's own products
):
    """Get products created by current user (for suppliers)"""
    return await ProductService.get_products_by_creator(user["user_id"], page, limit)


@router.get("/category/{category_id}")
async def get_products_by_category(
    category_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    user=Depends(get_current_user)
):
    return await ProductService.get_products_by_category(category_id, page, limit)


@router.get("/sku/{sku}")
async def get_product_by_sku(sku: str, user=Depends(get_current_user)):
    return await ProductService.get_product_by_sku(sku)


@router.get("/{product_id}")
async def get_product(product_id: str, user=Depends(get_current_user)):
    return await ProductService.get_product(product_id)


# ==================== UPDATE ====================

@router.put("/{product_id}")
async def update_product(
    product_id: str,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    category_id: Optional[str] = Form(None),
    subcategory_id: Optional[str] = Form(None),
    brand: Optional[str] = Form(None),
    supplier_ids: Optional[str] = Form(None),
    cost_price: Optional[float] = Form(None),
    selling_price: Optional[float] = Form(None),
    quantity: Optional[int] = Form(None),
    reorder_level: Optional[int] = Form(None),
    tax_percentage: Optional[float] = Form(None),
    unit: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    sku: Optional[str] = Form(None),
    user=Depends(require_roles(["admin", "supplier"]))  #  Admin & supplier
):
    #  Check ownership for suppliers
    await ProductService.check_product_permission(product_id, user)
    
    data = {}
    if name is not None: data["name"] = name
    if description is not None: data["description"] = description
    if category_id is not None: data["category_id"] = category_id if category_id else None
    if subcategory_id is not None: data["subcategory_id"] = subcategory_id if subcategory_id else None
    if brand is not None: data["brand"] = brand
    if supplier_ids is not None: data["supplier_ids"] = [s.strip() for s in supplier_ids.split(",") if s.strip()]
    if cost_price is not None: data["cost_price"] = cost_price
    if selling_price is not None: data["selling_price"] = selling_price
    if quantity is not None: data["quantity"] = quantity
    if reorder_level is not None: data["reorder_level"] = reorder_level
    if tax_percentage is not None: data["tax_percentage"] = tax_percentage
    if unit is not None: data["unit"] = unit
    if status is not None: data["status"] = status
    if tags is not None: data["tags"] = [t.strip() for t in tags.split(",") if t.strip()]
    if sku is not None: data["sku"] = sku

    return await ProductService.update_product(product_id, data, user["user_id"])


@router.put("/{product_id}/image")
async def update_product_image(
    product_id: str,
    file: UploadFile = File(...),
    user=Depends(require_roles(["admin", "supplier"]))
):
    #  Check ownership for suppliers
    await ProductService.check_product_permission(product_id, user)
    
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    filename = f"{uuid.uuid4()}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    image_url = f"/static/uploads/products/{filename}"
    image_metadata = {
        "filename": file.filename,
        "size": file_size,
        "content_type": file.content_type
    }

    return await ProductService.update_product_image(product_id, image_url, image_metadata, user["user_id"])


@router.patch("/{product_id}/quantity")
async def update_product_quantity(
    product_id: str,
    change: int = Form(...),
    user=Depends(require_roles(["admin", "supplier"]))
):
    # ✅ Check ownership for suppliers
    await ProductService.check_product_permission(product_id, user)
    
    return await ProductService.update_quantity(product_id, change, user["user_id"])


# ==================== DELETE (Admin only) ====================

@router.delete("/{product_id}")
async def delete_product(
    product_id: str, 
    user=Depends(require_roles(["admin"]))  #  Only admin can delete
):
    return await ProductService.delete_product(product_id)

# ==================== VARIANTS ====================

@router.post("/{product_id}/variants")
async def add_variant(
    product_id: str,
    name: str = Form(...),  # e.g., "Red - Large"
    attributes: str = Form("{}"),  # JSON string: {"color": "Red", "size": "Large"}
    price_adjustment: float = Form(0),
    quantity: int = Form(0),
    image_url: str = Form(""),
    user=Depends(require_roles(["admin", "supplier"]))
):
    import json
    try:
        attrs = json.loads(attributes) if attributes else {}
    except:
        attrs = {}
    
    data = {
        "name": name,
        "attributes": attrs,
        "price_adjustment": price_adjustment,
        "quantity": quantity,
        "image_url": image_url
    }
    return await ProductService.add_variant(product_id, data, user["user_id"])


@router.put("/{product_id}/variants/{variant_sku}")
async def update_variant(
    product_id: str,
    variant_sku: str,
    name: Optional[str] = Form(None),
    attributes: Optional[str] = Form(None),
    price_adjustment: Optional[float] = Form(None),
    quantity: Optional[int] = Form(None),
    image_url: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    user=Depends(require_roles(["admin", "supplier"]))
):
    import json
    data = {}
    if name: data["name"] = name
    if attributes:
        try:
            data["attributes"] = json.loads(attributes)
        except:
            pass
    if price_adjustment is not None: data["price_adjustment"] = price_adjustment
    if quantity is not None: data["quantity"] = quantity
    if image_url: data["image_url"] = image_url
    if status: data["status"] = status
    
    return await ProductService.update_variant(product_id, variant_sku, data, user["user_id"])


@router.patch("/{product_id}/variants/{variant_sku}/quantity")
async def update_variant_quantity(
    product_id: str,
    variant_sku: str,
    change: int = Form(...),
    user=Depends(require_roles(["admin", "supplier"]))
):
    return await ProductService.update_variant_quantity(product_id, variant_sku, change, user["user_id"])


@router.delete("/{product_id}/variants/{variant_sku}")
async def delete_variant(
    product_id: str,
    variant_sku: str,
    user=Depends(require_roles(["admin"]))
):
    return await ProductService.delete_variant(product_id, variant_sku, user["user_id"])