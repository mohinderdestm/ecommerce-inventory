from fastapi import APIRouter, Depends, UploadFile, File
from app.schemas.product_schema import ProductCreate, ProductUpdate
from app.services.product_service import ProductService
from app.repositories.product_repository import ProductRepository
from app.core.database import get_db
from app.core.dependencies import required_roles
import cloudinary.uploader
from bson import ObjectId


router = APIRouter(prefix="/products", tags=["Products"])

@router.post("/")
async def create_product(
    payload: ProductCreate,
    db=Depends(get_db),
    user=Depends(required_roles(["admin", "inventory_manager"]))
):
    service = ProductService(repo=ProductRepository(db))
    result = await service.create_product(payload, user)
    
    # RETURN THE CREATED PRODUCT 
    product_id = result["_id"]
    product = await service.get_product(product_id)
    return product

@router.post("/{product_id}/upload-image")
async def upload_image(
    product_id: str,
    file: UploadFile = File(...),
    db=Depends(get_db)
):
    try:
        result = cloudinary.uploader.upload(file.file, resource_type="auto")
    except Exception as e:
        return {"error": str(e)}

    image_url = result["secure_url"]

    await db["products"].update_one(
        {"_id": ObjectId(product_id)},
        {"$set": {"image_url": image_url}}
    )

    return {"image_url": image_url}


@router.post("/{product_id}/variants/{index}/upload-image")
async def upload_variant_image(
    product_id: str,
    index: int,
    file: UploadFile = File(...),
    db=Depends(get_db)
):
    try:
        result = cloudinary.uploader.upload(file.file)
    except Exception as e:
        return {"error": str(e)}

    image_url = result["secure_url"]

    await db["products"].update_one(
        {"_id": ObjectId(product_id)},
        {"$set": {f"variants.{index}.image_url": image_url}}
    )

    return {"image_url": image_url}


@router.get("/{product_id}")
async def get_product(product_id: str, db=Depends(get_db)):
    service = ProductService(ProductRepository(db))
    return await service.get_product(product_id)


@router.put("/{product_id}")
async def update_product(
    product_id: str,
    payload: ProductUpdate,
    db=Depends(get_db),
    user=Depends(required_roles(["admin","inventory_manager"]))
):
    service = ProductService(ProductRepository(db))
    await service.update_product(product_id, payload) 
    
    #  RETURN UPDATED PRODUCT 
    product = await service.get_product(product_id)
    return product


@router.delete("/{product_id}")
async def delete_product(
    product_id: str,
    db=Depends(get_db),
    user=Depends(required_roles(["admin"]))
):
    service = ProductService(ProductRepository(db))
    return await service.delete_product(product_id)


@router.get("/")
async def list_products(
    search: str = "",
    category: str = "",
    brand: str = "",
    min_price: float = 0,
    max_price: float = 0,
    color: str = "",
    size: str = "",
    in_stock: bool = False,
    sort_by: str = "created_at",
    order: str = "desc",
    skip: int = 0,
    limit: int = 10,
    db=Depends(get_db)
):
    filters = {"is_deleted": False}

    # 🔍 SEARCH (multi-field)
    if search:
        filters["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"brand": {"$regex": search, "$options": "i"}},
            {"category": {"$regex": search, "$options": "i"}},
            {"variants.sku": {"$regex": search, "$options": "i"}},
            {"variants.attributes.color": {"$regex": search, "$options": "i"}},
            {"variants.attributes.size": {"$regex": search, "$options": "i"}},
            {"variants.attributes.storage": {"$regex": search, "$options": "i"}}
        ]

    #  CATEGORY FILTER
    if category:
        filters["category"] = category

    #  BRAND FILTER
    if brand:
        filters["brand"] = brand

    #  PRICE FILTER
    if min_price or max_price:
        filters["selling_price"] = {}
        if min_price:
            filters["selling_price"]["$gte"] = min_price
        if max_price:
            filters["selling_price"]["$lte"] = max_price

    #  ATTRIBUTE FILTERS
    if color:
        filters["variants.attributes.color"] = color

    if size:
        filters["variants.attributes.size"] = size

    #  STOCK FILTER
    if in_stock:
          filters["variants"] = {
                 "$elemMatch": {"stock": {"$gt": 0}}
}

    repo = ProductRepository(db)
 
    #  SORTING
    sort_order = -1 if order == "desc" else 1

    cursor = repo.collection.find(filters) \
        .sort(sort_by, sort_order) \
        .skip(skip) \
        .limit(limit)

    data = await cursor.to_list(length=limit)

    #  TOTAL COUNT (IMPORTANT FIX)
    total = await repo.collection.count_documents(filters)

    #  FORMAT RESPONSE
    for item in data:
        item["id"] = str(item["_id"])
        del item["_id"]

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": data
    }