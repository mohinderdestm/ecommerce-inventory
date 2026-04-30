from fastapi import HTTPException
from app.repositories.warehouse_staff_repository import WarehouseStaffRepository
from app.repositories.warehouse_repository import WarehouseRepository
from app.repositories.staff_repository import StaffRepository
from app.models.warehouse_staff_model import WarehouseStaffModel
from app.services.audit_service import AuditService


class WarehouseStaffService:
    @staticmethod
    async def _enrich_assignment(assignment: dict):
        enriched = dict(assignment)
        staff = await StaffRepository.get_by_id(assignment.get("staff_id"))
        if staff:
            enriched["staff_name"] = staff.get("name")
            enriched["staff_email"] = staff.get("email")
            enriched["staff_phone"] = staff.get("phone")
            enriched["staff_role"] = staff.get("role")
            enriched["staff_is_active"] = staff.get("is_active", True)
        return enriched

    @staticmethod
    def check_manager(user):
        if user["role"] != "manager":
            raise HTTPException(status_code=403, detail="Only manager allowed")

    @staticmethod
    def check_admin_or_manager(user):
        if user["role"] not in ["manager", "admin"]:
            raise HTTPException(status_code=403, detail="Access denied")

    @staticmethod
    async def assign_staff(
        warehouse_id: str, staff_id: str, user, audit_context: dict | None = None
    ):
        WarehouseStaffService.check_manager(user)

        warehouse = await WarehouseRepository.get_by_id(warehouse_id)
        if not warehouse:
            raise HTTPException(status_code=404, detail="Warehouse not found")

        staff = await StaffRepository.get_by_id(staff_id)
        if not staff:
            raise HTTPException(status_code=404, detail="Staff not found")

        exists = await WarehouseStaffRepository.exists(warehouse_id, staff_id)
        if exists:
            raise HTTPException(status_code=400, detail="Staff already assigned")

        data = WarehouseStaffModel.create_dict(warehouse, staff)
        result = await WarehouseStaffRepository.assign(data)

        await WarehouseRepository.add_staff(warehouse_id, staff_id, staff.get("name"))

        created = await WarehouseStaffRepository.get_by_id(str(result.inserted_id))
        await AuditService.safe_log_action(
            user=user,
            action="warehouse_staff.assign",
            entity_type="warehouse_staff",
            entity_id=str(result.inserted_id),
            old_value=None,
            new_value=created,
            audit_context=audit_context,
        )

        return {"message": "Staff assigned successfully"}

    @staticmethod
    async def bulk_assign_staff(data, user, audit_context: dict | None = None):
        WarehouseStaffService.check_manager(user)

        warehouse = await WarehouseRepository.get_by_id(data.warehouse_id)
        if not warehouse:
            raise HTTPException(status_code=404, detail="Warehouse not found")

        assigned = []
        skipped = []

        for staff_id in data.staff_ids:

            staff = await StaffRepository.get_by_id(staff_id)
            if not staff:
                skipped.append({"staff_id": staff_id, "reason": "Not found"})
                continue

            exists = await WarehouseStaffRepository.exists(data.warehouse_id, staff_id)
            if exists:
                skipped.append({"staff_id": staff_id, "reason": "Already assigned"})
                continue

            mapping = WarehouseStaffModel.create_dict(warehouse, staff)

            await WarehouseStaffRepository.assign(mapping)

            await WarehouseRepository.add_staff(
                data.warehouse_id, staff_id, staff.get("name")
            )

            assigned.append(staff_id)

        await AuditService.safe_log_action(
            user=user,
            action="warehouse_staff.bulk_assign",
            entity_type="warehouse_staff",
            entity_id=data.warehouse_id,
            old_value=None,
            new_value={
                "warehouse_id": data.warehouse_id,
                "assigned_staff_ids": assigned,
                "skipped": skipped,
            },
            audit_context=audit_context,
        )

        return {
            "message": "Bulk assignment completed",
            "assigned_count": len(assigned),
            "skipped": skipped,
        }

    @staticmethod
    async def get_staff_by_warehouse(warehouse_id: str, user):
        WarehouseStaffService.check_admin_or_manager(user)

        assignments = await WarehouseStaffRepository.get_by_warehouse(warehouse_id)
        enriched_assignments = []
        for item in assignments:
            enriched_assignments.append(
                await WarehouseStaffService._enrich_assignment(item)
            )
        return [WarehouseStaffModel.response(item) for item in enriched_assignments]

    @staticmethod
    async def remove_staff(
        warehouse_id: str, staff_id: str, user, audit_context: dict | None = None
    ):
        WarehouseStaffService.check_manager(user)

        existing = await WarehouseStaffRepository.get_one(warehouse_id, staff_id)

        result = await WarehouseStaffRepository.remove(warehouse_id, staff_id)

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Assignment not found")

        await WarehouseRepository.remove_staff(warehouse_id, staff_id, None)

        await AuditService.safe_log_action(
            user=user,
            action="warehouse_staff.remove",
            entity_type="warehouse_staff",
            entity_id=f"{warehouse_id}:{staff_id}",
            old_value=existing,
            new_value=None,
            audit_context=audit_context,
        )

        return {"message": "Staff removed successfully"}

    @staticmethod
    async def get_all_assignments(user):
        WarehouseStaffService.check_admin_or_manager(user)

        assignments = await WarehouseStaffRepository.get_all()
        enriched_assignments = []
        for item in assignments:
            enriched_assignments.append(
                await WarehouseStaffService._enrich_assignment(item)
            )
        return [WarehouseStaffModel.response(item) for item in enriched_assignments]
