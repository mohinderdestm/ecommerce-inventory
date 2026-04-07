import os
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException

from app.modules.product_catalog.schemas import ProductCreate, VariantCreate
from app.modules.product_catalog.services import ProductService
from app.modules.product_catalog.variant_services import VariantService

from app.core.config import security
from app.db.database import product_collection, image_collection

router = APIRouter(prefix="/products", tags=["Products"])


# ✅ PRODUCT CRUD

@router.post("/")
async def create_product(product: ProductCreate, user=Depends(security.get_current_user)):
    return await ProductService.create_product(product.dict(), user["sub"])


@router.get("/")
async def get_products():
    return await ProductService.get_products()


@router.put("/{product_id}")
async def update_product(product_id: str, data: dict, user=Depends(security.get_current_user)):
    return await ProductService.update_product(product_id, data, user["sub"])


@router.delete("/{product_id}")
async def delete_product(product_id: str):
    return await ProductService.delete_product(product_id)


# ✅ VARIANTS

@router.post("/{product_id}/variants")
async def create_variant(product_id: str, variant: VariantCreate):
    return await VariantService.create_variant(product_id, variant.dict())


@router.get("/{product_id}/variants")
async def get_variants(product_id: str):
    return await VariantService.get_variants(product_id)


# ✅ SEARCH

@router.get("/search")
async def search(q: str):
    return await ProductService.search_products(q)


# ✅ FILTER

@router.get("/filter")
async def filter_products(category_id: str = None):
    query = {"status": True}
    if category_id:
        query["category_id"] = category_id

    results = []
    async for p in product_collection.find(query):
        p["id"] = p["_id"]
        del p["_id"]
        results.append(p)

    return results


# ✅ IMAGE UPLOAD

@router.post("/{product_id}/upload-image")
async def upload_image(product_id: str, file: UploadFile = File(...)):

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


# import os
# import uuid
# from datetime import datetime
# from fastapi import APIRouter, Depends, HTTPException
# from app.modules.product_catalog.schemas import ProductCreate
# from app.modules.product_catalog.services import ProductService
# from fastapi import UploadFile, File

# from app.core.config import security
# from app.db.database import image_collection, product_collection

# router = APIRouter(prefix="/products", tags=["Products"])

# @router.post("/")
# async def create_product(
#     product: ProductCreate,
#     user = Depends(security.get_current_user)
# ):
#     if user["role"] != "Admin":
#         raise HTTPException(status_code=403, detail="Only admin can add products")

#     return await ProductService.create_product(
#         product.dict(),
#         user["sub"]
#     )

# @router.get("/")
# async def get_products():
#     return await ProductService.get_products()

# @router.put("/{product_id}")
# async def update_product(
#     product_id: str,
#     product: dict,
#     user = Depends(security.get_current_user)
# ):
#     if user["role"] != "Admin":
#         raise HTTPException(status_code=403, detail="Only admin can update")

#     return await ProductService.update_product(
#         product_id,
#         product,
#         user["sub"]
#     )

# @router.delete("/{product_id}")
# async def delete_product(
#     product_id: str,
#     user = Depends(security.get_current_user)
# ):
#     if user["role"] != "Admin":
#         raise HTTPException(status_code=403, detail="Only admin can delete")

#     return await ProductService.delete_product(product_id)

# @router.post("/{product_id}/upload-image")
# async def upload_image(
#     product_id: str,
#     file: UploadFile = File(...),
#     user = Depends(security.get_current_user)
# ):
#     # ✅ Role check
#     if user["role"] != "Admin":
#         raise HTTPException(status_code=403, detail="Only admin can upload images")

#     # ✅ Check if product exists
#     product = await product_collection.find_one({"_id": product_id})
#     if not product:
#         raise HTTPException(status_code=404, detail="Product not found")

#     # ✅ Ensure uploads folder exists
#     upload_dir = "uploads"
#     os.makedirs(upload_dir, exist_ok=True)

#     # ✅ Generate unique filename
#     filename = f"{uuid.uuid4()}_{file.filename}"
#     file_location = os.path.join(upload_dir, filename)

#     # ✅ Save file locally
#     with open(file_location, "wb") as f:
#         f.write(await file.read())

#     # ✅ Save metadata in MongoDB
#     image_doc = {
#         "_id": str(uuid.uuid4()),
#         "product_id": product_id,
#         "image_url": file_location,
#         "created_at": datetime.utcnow()
#     }

#     await image_collection.insert_one(image_doc)

#     # ✅ Response
#     return {
#         "message": "Image uploaded successfully",
#         "image": {
#             "id": image_doc["_id"],
#             "product_id": product_id,
#             "image_url": file_location
#         }
#     }

# @router.get("/{product_id}/images")
# async def get_images(product_id: str):
#     return await ProductService.get_product_images(product_id)