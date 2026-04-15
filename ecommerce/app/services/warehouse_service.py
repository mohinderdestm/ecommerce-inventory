from typing import Optional
from datetime import datetime, timezone
from fastapi import HTTPException
import logging

from app.repositories.warehouse_repository import WarehouseRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.user_repository import UserRepository
from app.models.warehouse import (
    WarehouseStatus, TransferStatus,
    build_warehouse_document, build_stock_transfer_document,
)
from app.schemas.warehouse import (
    WarehouseCreateRequest, WarehouseUpdateRequest,
    StaffAssignRequest, StockUpdateRequest, StockTransferRequest,
)

logger = logging.getLogger(__name__)


class WarehouseService:
    def __init__(
        self,
        warehouse_repo: WarehouseRepository,
        product_repo: ProductRepository,
        user_repo: UserRepository,
    ):
        self.repo = warehouse_repo
        self.product_repo = product_repo
        self.user_repo = user_repo

    # Create 

    async def create_warehouse(
        self, payload: WarehouseCreateRequest, created_by: str
    ) -> dict:
        if await self.repo.name_exists(payload.name):
            raise HTTPException(
                status_code=409,
                detail="A warehouse with this name already exists."
            )
        doc = build_warehouse_document(
            name=payload.name,
            created_by=created_by,
            address=payload.address.model_dump() if payload.address else None,
            contact_person=payload.contact_person,
            phone=payload.phone,
            email=str(payload.email) if payload.email else None,
            capacity=payload.capacity,
            notes=payload.notes,
        )
        created = await self.repo.create(doc)
        logger.info(f"Warehouse '{created['name']}' created by {created_by}")
        return created

    # Read 

    async def get_warehouse(self, warehouse_id: str) -> dict:
        wh = await self.repo.find_by_id(warehouse_id)
        if not wh:
            raise HTTPException(status_code=404, detail="Warehouse not found.")
        return wh

    async def list_warehouses(
        self,
        status: Optional[str],
        search: Optional[str],
        page: int,
        page_size: int,
    ) -> dict:
        skip = (page - 1) * page_size
        warehouses, total = await self.repo.list_warehouses(
            status=status, search=search, skip=skip, limit=page_size
        )
        return {"total": total, "page": page, "page_size": page_size, "warehouses": warehouses}

    # Update 

    async def update_warehouse(
        self, warehouse_id: str, payload: WarehouseUpdateRequest, updated_by: str
    ) -> dict:
        wh = await self.repo.find_by_id(warehouse_id)
        if not wh:
            raise HTTPException(status_code=404, detail="Warehouse not found.")

        update_data: dict = {"updated_by": updated_by}

        if payload.name is not None:
            if await self.repo.name_exists(payload.name, exclude_id=warehouse_id):
                raise HTTPException(status_code=409, detail="Warehouse name already exists.")
            update_data["name"] = payload.name.strip()
        if payload.address is not None:
            update_data["address"] = payload.address.model_dump()
        if payload.contact_person is not None:
            update_data["contact_person"] = payload.contact_person
        if payload.phone is not None:
            update_data["phone"] = payload.phone
        if payload.email is not None:
            update_data["email"] = str(payload.email).lower()
        if payload.capacity is not None:
            update_data["capacity"] = payload.capacity
        if payload.notes is not None:
            update_data["notes"] = payload.notes
        if payload.status is not None:
            update_data["status"] = payload.status.value
            update_data["is_active"] = (payload.status == WarehouseStatus.ACTIVE)

        if len(update_data) == 1:
            raise HTTPException(status_code=400, detail="No valid fields provided.")

        updated = await self.repo.update(warehouse_id, update_data)
        logger.info(f"Warehouse {warehouse_id} updated by {updated_by}")
        return updated

    # Delete 

    async def delete_warehouse(self, warehouse_id: str) -> None:
        wh = await self.repo.find_by_id(warehouse_id)
        if not wh:
            raise HTTPException(status_code=404, detail="Warehouse not found.")

        # Block if warehouse has stock
        stock = await self.repo.get_warehouse_stock_summary(warehouse_id)
        if stock:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete warehouse — it holds stock for {len(stock)} product(s). Transfer or clear stock first."
            )
        await self.repo.delete(warehouse_id)
        logger.info(f"Warehouse {warehouse_id} deleted.")

    # Staff Assignment 

    async def assign_staff(
        self, warehouse_id: str, payload: StaffAssignRequest, updated_by: str
    ) -> dict:
        wh = await self.repo.find_by_id(warehouse_id)
        if not wh:
            raise HTTPException(status_code=404, detail="Warehouse not found.")

        # Validate all user IDs exist
        invalid = []
        for uid in payload.user_ids:
            if not await self.user_repo.find_by_id(uid):
                invalid.append(uid)
        if invalid:
            raise HTTPException(
                status_code=404,
                detail=f"These user IDs were not found: {invalid}"
            )

        updated = await self.repo.assign_staff(warehouse_id, payload.user_ids)
        logger.info(f"Assigned {len(payload.user_ids)} staff to warehouse {warehouse_id}")
        return updated

    async def unassign_staff(
        self, warehouse_id: str, payload: StaffAssignRequest, updated_by: str
    ) -> dict:
        wh = await self.repo.find_by_id(warehouse_id)
        if not wh:
            raise HTTPException(status_code=404, detail="Warehouse not found.")
        updated = await self.repo.unassign_staff(warehouse_id, payload.user_ids)
        logger.info(f"Unassigned {len(payload.user_ids)} staff from warehouse {warehouse_id}")
        return updated

    #  Stock Management 

    async def update_stock(
        self, warehouse_id: str, payload: StockUpdateRequest, updated_by: str
    ) -> dict:
        wh = await self.repo.find_by_id(warehouse_id)
        if not wh:
            raise HTTPException(status_code=404, detail="Warehouse not found.")
        if not wh["is_active"]:
            raise HTTPException(status_code=400, detail="Cannot update stock in an inactive warehouse.")

        # Validate product exists
        product = await self.product_repo.find_by_id(payload.product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found.")

        # Prevent negative stock
        if payload.quantity < 0:
            existing = await self.repo.get_stock_entry(
                warehouse_id, payload.product_id, payload.variant_id
            )
            current_qty = existing["quantity"] if existing else 0
            if current_qty + payload.quantity < 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient stock. Current: {current_qty}, Requested reduction: {abs(payload.quantity)}"
                )

        result = await self.repo.upsert_stock(
            warehouse_id=warehouse_id,
            product_id=payload.product_id,
            variant_id=payload.variant_id,
            quantity_delta=payload.quantity,
        )
        logger.info(
            f"Stock updated in warehouse {warehouse_id}: "
            f"product={payload.product_id} delta={payload.quantity} by {updated_by}"
        )
        return result

    async def get_stock_summary(self, warehouse_id: str) -> dict:
        
        wh = await self.repo.find_by_id(warehouse_id)
        if not wh:
            raise HTTPException(status_code=404, detail="Warehouse not found.")

        stock_entries = await self.repo.get_warehouse_stock_summary(warehouse_id)

        # Enrich with product info
        enriched = []
        for entry in stock_entries:
            product = await self.product_repo.find_by_id(entry["product_id"])
            enriched.append({
                **entry,
                "product_name": product["name"] if product else "Unknown",
                "sku": product["sku"] if product else "—",
            })

        return {
            "warehouse_id": warehouse_id,
            "warehouse_name": wh["name"],
            "total_items": len(enriched),
            "stock": enriched,
        }

    async def get_product_stock_across_warehouses(self, product_id: str) -> list[dict]:
        
        product = await self.product_repo.find_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found.")

        entries = await self.repo.get_product_stock_across_warehouses(product_id)

        # Enrich with warehouse names
        enriched = []
        for entry in entries:
            wh = await self.repo.find_by_id(entry["warehouse_id"])
            enriched.append({
                **entry,
                "warehouse_name": wh["name"] if wh else "Unknown",
            })
        return enriched

    # Stock Transfer 

    async def initiate_transfer(
        self, from_warehouse_id: str, payload: StockTransferRequest, created_by: str
    ) -> dict:
        # Validate both warehouses
        from_wh = await self.repo.find_by_id(from_warehouse_id)
        if not from_wh or not from_wh["is_active"]:
            raise HTTPException(status_code=404, detail="Source warehouse not found or inactive.")

        to_wh = await self.repo.find_by_id(payload.to_warehouse_id)
        if not to_wh or not to_wh["is_active"]:
            raise HTTPException(status_code=404, detail="Destination warehouse not found or inactive.")

        if from_warehouse_id == payload.to_warehouse_id:
            raise HTTPException(status_code=400, detail="Source and destination warehouse cannot be the same.")

        # Check source has enough stock
        existing = await self.repo.get_stock_entry(
            from_warehouse_id, payload.product_id, payload.variant_id
        )
        current_qty = existing["quantity"] if existing else 0
        if current_qty < payload.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock in source warehouse. Available: {current_qty}, Requested: {payload.quantity}"
            )

        # Create transfer record
        transfer_doc = build_stock_transfer_document(
            from_warehouse_id=from_warehouse_id,
            to_warehouse_id=payload.to_warehouse_id,
            product_id=payload.product_id,
            variant_id=payload.variant_id,
            quantity=payload.quantity,
            created_by=created_by,
            notes=payload.notes,
        )
        transfer = await self.repo.create_transfer(transfer_doc)

        # Immediately deduct from source and add to destination (direct transfer)
        await self.repo.upsert_stock(from_warehouse_id, payload.product_id, payload.variant_id, -payload.quantity)
        await self.repo.upsert_stock(payload.to_warehouse_id, payload.product_id, payload.variant_id, payload.quantity)

        # Mark transfer as completed
        completed = await self.repo.update_transfer(transfer["_id"], {
            "status": TransferStatus.COMPLETED.value,
            "completed_by": created_by,
            "completed_at": datetime.now(timezone.utc),
        })

        logger.info(
            f"Stock transfer {transfer['_id']}: {payload.quantity} units of "
            f"{payload.product_id} from {from_warehouse_id} → {payload.to_warehouse_id}"
        )
        return completed

    async def list_transfers(
        self,
        warehouse_id: Optional[str],
        status: Optional[str],
        page: int,
        page_size: int,
    ) -> dict:
        skip = (page - 1) * page_size
        transfers, total = await self.repo.list_transfers(
            warehouse_id=warehouse_id, status=status, skip=skip, limit=page_size
        )
        return {"total": total, "page": page, "page_size": page_size, "transfers": transfers}