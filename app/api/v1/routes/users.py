from fastapi import APIRouter, Depends
from app.utils.dependencies import get_current_user, require_role
from app.core.database import db

router = APIRouter()


@router.get("/me")
async def get_me(user=Depends(get_current_user)):

    user_data = dict(user) if not isinstance(user, dict) else user

    if user_data.get("role") == "supplier":

        supplier_info = await db["suppliers"].find_one(
            {"email": user_data.get("email")}
        )
        if supplier_info:

            user_data["supplier_details"] = {
                "name": supplier_info.get("name"),
                "contact_person": supplier_info.get("contact_person"),
                "phone": supplier_info.get("phone"),
                "gst": supplier_info.get("gst"),
                "address": supplier_info.get("address"),
                "payment_terms": supplier_info.get("payment_terms"),
                "rating": supplier_info.get("rating", 0),
            }

    return {"message": "User info", "user": user_data}


@router.get("/admin-only")
async def admin_data(user=Depends(require_role(["admin"]))):
    return {"message": "Welcome Admin", "user": user}


@router.get("/manager-data")
async def manager_data(user=Depends(require_role(["admin", "manager"]))):
    return {"message": "Manager access granted", "user": user}
