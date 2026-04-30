from app.repositories.user_repository import UserRepository
from app.repositories.supplier_repository import SupplierRepository
from app.models.supplier_model import supplier_model
from app.core.security import hash_password, verify_password, create_access_token
from datetime import datetime
from app.services.audit_service import AuditService

supplier_repo = SupplierRepository()


class UserService:

    @staticmethod
    async def register(user_data: dict, audit_context: dict | None = None):

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
            "role": user_data.get("role", "viewer"),
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
            supplier_id = await supplier_repo.create(formatted_supplier)
            await AuditService.safe_log_action(
                user={
                    "id": user_id_str,
                    "email": user_data["email"],
                    "role": user_data.get("role", "viewer"),
                    "name": display_name,
                },
                action="supplier.create",
                entity_type="supplier",
                entity_id=supplier_id,
                old_value=None,
                new_value=formatted_supplier,
                audit_context=audit_context,
            )

        await AuditService.safe_log_action(
            user={
                "id": user_id_str,
                "email": user_data["email"],
                "role": user_data.get("role", "viewer"),
                "name": display_name,
            },
            action="auth.register",
            entity_type="user",
            entity_id=user_id_str,
            old_value=None,
            new_value={
                "name": display_name,
                "email": user_data["email"],
                "role": user_data.get("role", "viewer"),
            },
            audit_context=audit_context,
        )

        return {"message": "User registered successfully"}

    @staticmethod
    async def login(email: str, password: str, audit_context: dict | None = None):

        user = await UserRepository.get_user_by_email(email)

        if not user:
            return None

        if not verify_password(password, user.get("password", "")):
            return None

        user_role = user.get("role", "viewer")
        user_name = user.get("name", "User")

        access_token = create_access_token(
            data={"sub": user["email"], "role": user_role, "name": user_name}
        )

        await AuditService.safe_log_action(
            user={
                "id": str(user["_id"]),
                "email": user["email"],
                "role": user_role,
                "name": user_name,
            },
            action="auth.login",
            entity_type="user",
            entity_id=str(user["_id"]),
            old_value=None,
            new_value={"email": user["email"], "role": user_role},
            audit_context=audit_context,
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "email": user["email"],
            "role": user_role,
            "name": user_name,
        }
