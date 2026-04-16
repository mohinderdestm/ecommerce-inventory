from fastapi import HTTPException
from app.repositories.warehouse_staff_repository import WarehouseStaffRepository
from app.repositories.warehouse_repository import WarehouseRepository
from app.repositories.staff_repository import StaffRepository
from app.models.warehouse_staff_model import WarehouseStaffModel


class WarehouseStaffService:

    @staticmethod
    def check_manager(user):
        if user["role"] != "manager":
            raise HTTPException(status_code=403, detail="Only manager allowed")

    @staticmethod
    def check_admin_or_manager(user):
        if user["role"] not in ["manager", "admin"]:
            raise HTTPException(status_code=403, detail="Access denied")

    @staticmethod
    async def assign_staff(warehouse_id: str, staff_id: str, user):
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
        await WarehouseStaffRepository.assign(data)

        await WarehouseRepository.add_staff(warehouse_id, staff_id, staff.get("name"))

        return {"message": "Staff assigned successfully"}

    @staticmethod
    async def bulk_assign_staff(data, user):
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

        return {
            "message": "Bulk assignment completed",
            "assigned_count": len(assigned),
            "skipped": skipped,
        }

    @staticmethod
    async def get_staff_by_warehouse(warehouse_id: str, user):
        WarehouseStaffService.check_admin_or_manager(user)

        assignments = await WarehouseStaffRepository.get_by_warehouse(warehouse_id)

        return [WarehouseStaffModel.response(item) for item in assignments]

    @staticmethod
    async def remove_staff(warehouse_id: str, staff_id: str, user):
        WarehouseStaffService.check_manager(user)

        result = await WarehouseStaffRepository.remove(warehouse_id, staff_id)

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Assignment not found")

        await WarehouseRepository.remove_staff(warehouse_id, staff_id, None)

        return {"message": "Staff removed successfully"}

    @staticmethod
    async def get_all_assignments(user):
        WarehouseStaffService.check_admin_or_manager(user)

        assignments = await WarehouseStaffRepository.get_all()

        return [WarehouseStaffModel.response(item) for item in assignments]
