from datetime import datetime
from fastapi import HTTPException
from app.repositories.warehouse_repository import WarehouseRepository
from app.repositories.warehouse_staff_repository import WarehouseStaffRepository
from app.repositories.staff_repository import StaffRepository
from app.models.warehouse_model import WarehouseModel
from app.services.audit_service import AuditService


class WarehouseService:

    @staticmethod
    def check_manager(user):
        if user["role"] != "manager":
            raise HTTPException(status_code=403, detail="Only manager allowed")

    @staticmethod
    def check_view_access(user):
        if user["role"] not in ["manager", "admin", "supplier"]:
            raise HTTPException(status_code=403, detail="Access denied")

    @staticmethod
    async def create_warehouse(data, user, audit_context: dict | None = None):
        WarehouseService.check_manager(user)

        existing = await WarehouseRepository.exists_by_code(data.code)
        if existing:
            raise HTTPException(status_code=400, detail="Warehouse code already exists")

        warehouse_dict = WarehouseModel.warehouse_dict(data.dict(), user)

        warehouse_id = await WarehouseRepository.create(warehouse_dict)

        await AuditService.safe_log_action(
            user=user,
            action="warehouse.create",
            entity_type="warehouse",
            entity_id=warehouse_id,
            old_value=None,
            new_value=await WarehouseRepository.get_by_id(warehouse_id),
            audit_context=audit_context,
        )

        return {"message": "Warehouse created", "id": warehouse_id}

    @staticmethod
    async def _get_staff_for_warehouse(warehouse_id: str):
        assignments = await WarehouseStaffRepository.get_by_warehouse(warehouse_id)

        staff_list = []

        for a in assignments:
            staff = await StaffRepository.get_by_id(a.get("staff_id"))
            if staff:
                staff_list.append(
                    {
                        "id": str(staff["_id"]),
                        "name": staff.get("name"),
                        "email": staff.get("email"),
                        "role": staff.get("role"),
                        "phone": staff.get("phone"),
                        "is_active": staff.get("is_active"),
                    }
                )

        return staff_list

    @staticmethod
    async def get_all_warehouses(user):
        WarehouseService.check_view_access(user)

        warehouses = await WarehouseRepository.get_all()

        response = []

        for w in warehouses:
            warehouse_data = WarehouseModel.response(w)

            staff_list = await WarehouseService._get_staff_for_warehouse(str(w["_id"]))
            warehouse_data["staff"] = staff_list

            response.append(warehouse_data)

        return response

    @staticmethod
    async def get_warehouse(warehouse_id, user):
        WarehouseService.check_view_access(user)

        warehouse = await WarehouseRepository.get_by_id(warehouse_id)
        if not warehouse:
            raise HTTPException(status_code=404, detail="Warehouse not found")

        response = WarehouseModel.response(warehouse)

        staff_list = await WarehouseService._get_staff_for_warehouse(warehouse_id)
        response["staff"] = staff_list

        return response

    @staticmethod
    async def update_warehouse(
        warehouse_id, data, user, audit_context: dict | None = None
    ):
        WarehouseService.check_manager(user)

        warehouse = await WarehouseRepository.get_by_id(warehouse_id)
        if not warehouse:
            raise HTTPException(status_code=404, detail="Warehouse not found")

        incoming = data.dict(exclude_unset=True)

        update_data = {}

        def safe_update(field, old_value):
            new_value = incoming.get(field)
            if new_value not in [None, "", "string"]:
                return new_value
            return old_value

        update_data["name"] = safe_update("name", warehouse.get("name"))
        update_data["code"] = safe_update("code", warehouse.get("code"))
        update_data["email"] = safe_update("email", warehouse.get("email"))
        update_data["phone"] = safe_update("phone", warehouse.get("phone"))

        address = warehouse.get("address", {})

        address["street"] = safe_update("street", address.get("street"))
        address["city"] = safe_update("city", address.get("city"))
        address["state"] = safe_update("state", address.get("state"))
        address["country"] = safe_update("country", address.get("country"))
        address["pincode"] = safe_update("pincode", address.get("pincode"))

        update_data["address"] = address

        if incoming.get("capacity") is not None:
            update_data["capacity"] = incoming["capacity"]
        else:
            update_data["capacity"] = warehouse.get("capacity")

        if incoming.get("is_active") is not None:
            update_data["is_active"] = incoming["is_active"]
        else:
            update_data["is_active"] = warehouse.get("is_active")

        update_data["updated_at"] = datetime.utcnow()

        await WarehouseRepository.update(warehouse_id, update_data)

        await AuditService.safe_log_action(
            user=user,
            action="warehouse.update",
            entity_type="warehouse",
            entity_id=warehouse_id,
            old_value=warehouse,
            new_value=await WarehouseRepository.get_by_id(warehouse_id),
            audit_context=audit_context,
        )

        return {"message": "Warehouse updated successfully"}

    @staticmethod
    async def delete_warehouse(warehouse_id, user, audit_context: dict | None = None):
        WarehouseService.check_manager(user)

        warehouse = await WarehouseRepository.get_by_id(warehouse_id)
        if not warehouse:
            raise HTTPException(status_code=404, detail="Warehouse not found")

        await WarehouseRepository.delete(warehouse_id)

        await AuditService.safe_log_action(
            user=user,
            action="warehouse.delete",
            entity_type="warehouse",
            entity_id=warehouse_id,
            old_value=warehouse,
            new_value=None,
            audit_context=audit_context,
        )

        return {"message": "Warehouse deleted"}

    @staticmethod
    async def bulk_create_warehouses(data, user, audit_context: dict | None = None):
        WarehouseService.check_manager(user)

        created = []
        skipped = []

        for item in data.warehouses:
            existing = await WarehouseRepository.exists_by_code(item.code)

            if existing:
                skipped.append(item.code)
                continue

            warehouse_dict = WarehouseModel.warehouse_dict(item.dict(), user)

            result = await WarehouseRepository.create(warehouse_dict)
            created.append(str(result))

        await AuditService.safe_log_action(
            user=user,
            action="warehouse.bulk_create",
            entity_type="warehouse",
            entity_id=None,
            old_value=None,
            new_value={
                "created_ids": created,
                "skipped_codes": skipped,
                "created_count": len(created),
                "skipped_count": len(skipped),
            },
            audit_context=audit_context,
        )

        return {
            "message": "Bulk warehouse creation completed",
            "created_count": len(created),
            "skipped_count": len(skipped),
            "created_ids": created,
            "skipped_codes": skipped,
        }
