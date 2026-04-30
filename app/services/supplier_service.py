from datetime import datetime
from app.repositories.supplier_repository import SupplierRepository
from app.models.supplier_model import supplier_model
from app.services.audit_service import AuditService

repo = SupplierRepository()


class SupplierService:

    async def create_supplier(
        self, supplier_data, user: dict, audit_context: dict | None = None
    ):
        data = supplier_model(supplier_data.dict())
        supplier_id = await repo.create(data)
        await AuditService.safe_log_action(
            user=user,
            action="supplier.create",
            entity_type="supplier",
            entity_id=supplier_id,
            old_value=None,
            new_value=await repo.get_by_id(supplier_id),
            audit_context=audit_context,
        )
        return supplier_id

    async def get_suppliers(self):
        return await repo.get_all()

    async def get_supplier(self, supplier_id):
        supplier = await repo.get_by_id(supplier_id)
        if not supplier:
            raise Exception("Supplier not found")
        return supplier

    async def update_supplier(
        self,
        supplier_id,
        supplier_update,
        user: dict,
        audit_context: dict | None = None,
    ):
        existing = await repo.get_by_id(supplier_id)

        if not existing:
            raise Exception("Supplier not found")

        update_data = supplier_update.dict(exclude_unset=True)

        update_data = {
            k: v
            for k, v in update_data.items()
            if v not in [None, "", "string", "user@example.com"]
        }

        if not update_data:
            raise Exception("No valid fields provided for update")

        update_data["updated_at"] = datetime.utcnow()

        print("FINAL UPDATE DATA:", update_data)

        updated = await repo.update(supplier_id, update_data)
        await AuditService.safe_log_action(
            user=user,
            action="supplier.update",
            entity_type="supplier",
            entity_id=supplier_id,
            old_value=existing,
            new_value=updated,
            audit_context=audit_context,
        )
        return updated

    async def delete_supplier(
        self, supplier_id, user: dict, audit_context: dict | None = None
    ):
        existing = await repo.get_by_id(supplier_id)
        result = await repo.delete(supplier_id)
        await AuditService.safe_log_action(
            user=user,
            action="supplier.delete",
            entity_type="supplier",
            entity_id=supplier_id,
            old_value=existing,
            new_value=None,
            audit_context=audit_context,
        )
        return result
