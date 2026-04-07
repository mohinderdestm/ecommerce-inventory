import os
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException

from app.modules.product_catalog.schemas import ProductCreate, VariantCreate
from app.modules.product_catalog.services import ProductService
from app.modules.product_catalog.variant_services import VariantService
from app.modules.product_catalog.schemas import ProductUpdate

from app.core.config import RoleChecker
from app.db.database import product_collection, image_collection, variant_collection

router = APIRouter(prefix="/products", tags=["Products"])

admin_only = RoleChecker(["Admin"])
admin_manager = RoleChecker(["Admin", "Inventory Manager"])


@router.post("/")
async def create_product(
    product: ProductCreate,
    user=Depends(admin_manager)
):
    return await ProductService.create_product(product.dict(), user["sub"])


@router.get("/")
async def get_products():
    return await ProductService.get_products()


@router.put("/{product_id}")
async def update_product(
    product_id: str,
    product: ProductUpdate,
    user=Depends(admin_manager)
):
    return await ProductService.update_product(
        product_id,
        product.dict(exclude_unset=True),
        user["sub"]
    )


@router.delete("/{product_id}")
async def delete_product(
    product_id: str,
    user=Depends(admin_only)
):
    return await ProductService.delete_product(product_id)



@router.post("/{product_id}/variants")
async def create_variant(
    product_id: str,
    variant: VariantCreate,
    user=Depends(admin_manager)
):
    return await VariantService.create_variant(product_id, variant.dict())


@router.get("/{product_id}/variants")
async def get_variants(product_id: str):
    return await VariantService.get_variants(product_id)



@router.get("/search")
async def search(q: str):
    return await ProductService.search_products(q)


@router.get("/filter")
async def filter_products(category_id: str = None):

    query = {"status": True}

    if category_id:
        query["category_id"] = category_id

    results = []

    async for product in product_collection.find(query):

        product["id"] = product["_id"]
        del product["_id"]

        # 🔥 fetch variants
        variants = []
        async for v in variant_collection.find({"product_id": product["id"]}):
            v["id"] = v["_id"]
            del v["_id"]
            variants.append(v)

        product["variants"] = variants  # ✅ attach variants

        results.append(product)

    return results


@router.post("/{product_id}/upload-image")
async def upload_image(
    product_id: str,
    file: UploadFile = File(...),
    user=Depends(admin_manager)
):
    product = await product_collection.find_one({"_id": product_id})
    if not product:
        raise HTTPException(404, "Product not found")

    os.makedirs("uploads", exist_ok=True)

    filename = f"{uuid.uuid4()}_{file.filename}"
    path = os.path.join("uploads", filename)

    with open(path, "wb") as f:
        f.write(await file.read())

    image = {
        "_id": str(uuid.uuid4()),
        "product_id": product_id,
        "image_url": path,
        "created_at": datetime.utcnow()
    }

    await image_collection.insert_one(image)

    return {"message": "Uploaded", "image": image}


@router.get("/{product_id}/images")
async def get_images(product_id: str):
    images = []
    async for img in image_collection.find({"product_id": product_id}):
        img["id"] = img["_id"]
        del img["_id"]
        images.append(img)
    return images
