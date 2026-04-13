from datetime import datetime

class SupplierService:
    def __init__(self, repo):
        self.repo = repo

    async def create_supplier_for_user(self, user_id, payload):
        supplier_data = {
              "name": payload.get("name"),
               "email": payload.get("email"),
               "user_id": str(user_id),
               "created_at": datetime.utcnow(),
               "is_active": True
        }

        return await self.repo.create(supplier_data)

    async def get_supplier_by_user(self, user):
        return await self.repo.get_by_user_id(user["_id"])