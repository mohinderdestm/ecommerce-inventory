from datetime import datetime
from app.repositories.supplier_repository import SupplierRepository
from app.models.supplier_model import supplier_model

repo = SupplierRepository()


class SupplierService:

    async def create_supplier(self, supplier_data):
        data = supplier_model(supplier_data.dict())
        return await repo.create(data)

    async def get_suppliers(self):
        return await repo.get_all()

    async def get_supplier(self, supplier_id):
        supplier = await repo.get_by_id(supplier_id)
        if not supplier:
            raise Exception("Supplier not found")
        return supplier

    async def update_supplier(self, supplier_id, supplier_update):
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

        return await repo.update(supplier_id, update_data)

    async def delete_supplier(self, supplier_id):
        return await repo.delete(supplier_id)
