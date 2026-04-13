from fastapi import APIRouter, Depends,HTTPException
from app.core.database import get_db
from app.core.dependencies import required_roles
from app.repositories.supplier_repository import SupplierRepository
from app.services.supplier_service import SupplierService
from app.schemas.supplier_schema import SupplierCreate,SupplierUpdate

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])


# 🔥 CREATE SUPPLIER (with full details)
@router.post("/create")
async def create_supplier(
    payload: SupplierCreate,
    db=Depends(get_db),
    user=Depends(required_roles(["supplier"]))
):
    service = SupplierService(SupplierRepository(db))

    return await service.create_supplier_for_user(user, payload)


# 🔹 GET MY SUPPLIER
@router.get("/me")
async def get_my_supplier(
    db=Depends(get_db),
    user=Depends(required_roles(["supplier"]))
):
    service = SupplierService(SupplierRepository(db))
    supplier = await service.get_supplier_by_user(user)
    if supplier:
        supplier["_id"] = str(supplier["_id"])
        supplier["user_id"] = str(supplier["user_id"])
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier


# 🔹 update SUPPLIER profile
@router.put("/me")
async def update_supplier(
    payload: SupplierUpdate,
    db=Depends(get_db),
    user=Depends(required_roles(["supplier"]))
):
    repo = SupplierRepository(db)
    supplier = await repo.get_by_user_id(user["_id"])
    
    update_data = payload.dict(exclude_unset=True)

    await repo.collection.update_one(
        {"_id": supplier["_id"]},
        {"$set": update_data}
    )

    return {"message": "Supplier updated"}


#🔹 ADMIN: GET ALL SUPPLIERS
@router.get("/")
async def list_suppliers(
    db=Depends(get_db),
    user=Depends(required_roles(["admin"]))
):
    suppliers = await db["suppliers"].find().to_list(100)

    for s in suppliers:
        s["_id"] = str(s["_id"])

    return suppliers

@router.get("/my-products")
async def my_products(
    db=Depends(get_db),
    user=Depends(required_roles(["supplier"]))
):
    supplier_repo = SupplierRepository(db)
    supplier_service = SupplierService(supplier_repo)

    supplier = await supplier_service.get_supplier_by_user(user)

    if not supplier:
        return []

    products = await db["products"].find({
        "supplier_id": str(supplier["_id"])
    }).to_list(100)

    for p in products:
        p["_id"] = str(p["_id"])

    return products


@router.get("/with-products")
async def suppliers_with_products(db=Depends(get_db)):
    data = await db["suppliers"].aggregate([
        {
            "$lookup": {
                "from": "products",
                "localField": "_id",
                "foreignField": "supplier_id",
                "as": "products"
            }
        }
    ]).to_list(100)

    for s in data:
        s["_id"] = str(s["_id"])
        for p in s["products"]:
            p["_id"] = str(p["_id"])

    return data