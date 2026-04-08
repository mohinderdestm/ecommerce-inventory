from app.repositories.user_repository import UserRepository
from app.repositories.supplier_repository import SupplierRepository
from app.models.supplier_model import supplier_model
from app.core.security import hash_password
from datetime import datetime

supplier_repo = SupplierRepository()


class UserService:

    @staticmethod
    async def register(user_data: dict):
        existing = await UserRepository.get_user_by_email(user_data["email"])
        if existing:
            raise Exception("User already exists")

        display_name = user_data.get("name", "User")
        if user_data.get("role") == "supplier" and user_data.get("contact_person"):
            display_name = user_data.get("contact_person")

        auth_data = {
            "name": display_name,
            "email": user_data["email"],
            "password": hash_password(user_data["password"]),
            "role": user_data["role"],
            "created_at": datetime.utcnow(),
        }

        new_user = await UserRepository.create_user(auth_data)
        user_id_str = str(new_user.inserted_id)

        if user_data.get("role") == "supplier":
            business_data = {
                "name": user_data.get("name"),
                "email": user_data.get("email"),
                "phone": user_data.get("phone", "N/A"),
                "address": user_data.get("address", "N/A"),
                "gst": user_data.get("gst", "N/A"),
                "contact_person": user_data.get(
                    "contact_person", user_data.get("name")
                ),
                "payment_terms": user_data.get("payment_terms", "N/A"),
                "user_id": user_id_str,
            }
            formatted_supplier = supplier_model(business_data)
            await supplier_repo.create(formatted_supplier)

        return {"message": "User registered successfully"}
