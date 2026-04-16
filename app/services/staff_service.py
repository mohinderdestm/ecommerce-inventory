from fastapi import HTTPException
from datetime import datetime
from app.repositories.staff_repository import StaffRepository
from app.models.staff_model import StaffModel


class StaffService:

    @staticmethod
    def check_manager(user):
        if user["role"] != "manager":
            raise HTTPException(status_code=403, detail="Only manager allowed")

    @staticmethod
    def check_admin_or_manager(user):
        if user["role"] not in ["manager", "admin"]:
            raise HTTPException(status_code=403, detail="Access denied")

    @staticmethod
    async def create_staff(data, user):
        StaffService.check_manager(user)

        existing = await StaffRepository.get_by_email(data.email)
        if existing:
            raise HTTPException(status_code=400, detail="Email already exists")

        staff_data = StaffModel.create_dict(data.dict(), user)

        result = await StaffRepository.create(staff_data)

        return {"message": "Staff created", "id": str(result.inserted_id)}

    @staticmethod
    async def get_all_staff(user):
        StaffService.check_admin_or_manager(user)

        data = await StaffRepository.get_all()
        return [StaffModel.response(d) for d in data]

    @staticmethod
    async def update_staff(staff_id, data, user):
        StaffService.check_manager(user)

        existing = await StaffRepository.get_by_id(staff_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Staff not found")

        update_data = data.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()

        await StaffRepository.update(staff_id, update_data)

        return {"message": "Staff updated"}

    @staticmethod
    async def delete_staff(staff_id, user):
        StaffService.check_manager(user)

        existing = await StaffRepository.get_by_id(staff_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Staff not found")

        await StaffRepository.delete(staff_id)

        return {"message": "Staff deleted"}

    @staticmethod
    async def bulk_create_staff(data, user):
        StaffService.check_manager(user)

        created = []
        skipped = []

        for item in data.staff:
            existing = await StaffRepository.get_by_email(item.email)

            if existing:
                skipped.append(item.email)
                continue

            staff_data = StaffModel.create_dict(item.dict(), user)

            result = await StaffRepository.create(staff_data)
            created.append(str(result.inserted_id))

        return {
            "message": "Bulk staff creation completed",
            "created_count": len(created),
            "skipped_count": len(skipped),
            "created_ids": created,
            "skipped_emails": skipped,
        }
