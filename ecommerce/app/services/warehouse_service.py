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
from app.repositories.inventory_movement_repository import InventoryMovementRepository
from app.models.inventory_movement import build_inventory_movement_document, MovementType
from app.services.email_service import EmailService
from app.core.database import get_database
from app.services.audit_log_service import AuditLogService
from app.repositories.audit_log_repository import AuditLogRepository

logger = logging.getLogger(__name__)

def get_audit_log_svc() -> AuditLogService:
    db = get_database()
    return AuditLogService(AuditLogRepository(db))


class WarehouseService:
    def __init__(
        self,
        warehouse_repo: WarehouseRepository,
        product_repo: ProductRepository,
        user_repo: UserRepository,
        movement_repo: InventoryMovementRepository = None,
        email_service: EmailService = None,
    ):
        self.repo = warehouse_repo
        self.product_repo = product_repo
        self.user_repo = user_repo
        self.movement_repo = movement_repo
        self.email_service = email_service

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

    async def check_and_trigger_low_stock_alert(self, product_id: str):
        product = await self.product_repo.find_by_id(product_id)
        if not product or product.get("reorder_level", 0) <= 0:
            return

        reorder_level = product["reorder_level"]
        entries = await self.repo.get_product_stock_across_warehouses(product_id)
        total_stock = sum(entry["quantity"] for entry in entries)

        alert_sent = product.get("low_stock_alert_sent", False)

        if total_stock <= reorder_level and not alert_sent:
            # Trigger alert
            await self.product_repo.set_low_stock_alert_status(product_id, True)
            if self.email_service and self.user_repo:
                admins = await self.user_repo.get_admins_and_managers()
                admin_emails = [admin.get("email") for admin in admins if admin.get("email")]
                if admin_emails:
                    self.email_service.send_low_stock_alert(
                        admin_emails, product["name"], product["sku"], total_stock, reorder_level
                    )
            logger.info(f"Low stock alert triggered for product {product['sku']} (Stock: {total_stock})")
            
        elif total_stock > reorder_level and alert_sent:
            # Reset alert
            await self.product_repo.set_low_stock_alert_status(product_id, False)
            logger.info(f"Low stock alert reset for product {product['sku']} (Stock: {total_stock})")

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
        existing = await self.repo.get_stock_entry(
            warehouse_id, payload.product_id, payload.variant_id
        )
        current_qty = existing["quantity"] if existing else 0
        
        if payload.quantity < 0:
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

        if self.movement_repo:
            mtype = MovementType.INWARD if payload.quantity >= 0 else MovementType.OUTWARD
            doc = build_inventory_movement_document(
                product_id=payload.product_id,
                warehouse_id=warehouse_id,
                movement_type=mtype,
                quantity=abs(payload.quantity),
                reference_type="MANUAL_UPDATE",
                performed_by=updated_by,
                variant_id=payload.variant_id,
                remarks=f"Manual update via warehouse stock API"
            )
            await self.movement_repo.create(doc)

        try:
            await get_audit_log_svc().log_action(
                user_id=updated_by,
                action="update_stock",
                entity_type="warehouse_stock",
                entity_id=f"{warehouse_id}_{payload.product_id}",
                old_value={"quantity": current_qty},
                new_value=result
            )
        except Exception as e:
            logger.error(f"Failed to log audit action: {e}")

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

        if self.movement_repo:
            # TRANSFER_OUT
            doc_out = build_inventory_movement_document(
                product_id=payload.product_id,
                warehouse_id=from_warehouse_id,
                movement_type=MovementType.TRANSFER_OUT,
                quantity=payload.quantity,
                reference_type="TRANSFER",
                reference_id=str(transfer["_id"]),
                performed_by=created_by,
                variant_id=payload.variant_id,
                remarks=f"Transfer to {payload.to_warehouse_id}"
            )
            await self.movement_repo.create(doc_out)

            # TRANSFER_IN
            doc_in = build_inventory_movement_document(
                product_id=payload.product_id,
                warehouse_id=payload.to_warehouse_id,
                movement_type=MovementType.TRANSFER_IN,
                quantity=payload.quantity,
                reference_type="TRANSFER",
                reference_id=str(transfer["_id"]),
                performed_by=created_by,
                variant_id=payload.variant_id,
                remarks=f"Transfer from {from_warehouse_id}"
            )
            await self.movement_repo.create(doc_in)

        # Mark transfer as completed
        completed = await self.repo.update_transfer(transfer["_id"], {
            "status": TransferStatus.COMPLETED.value,
            "completed_by": created_by,
            "completed_at": datetime.now(timezone.utc),
        })

        try:
            await get_audit_log_svc().log_action(
                user_id=created_by,
                action="warehouse_transfer",
                entity_type="stock_transfer",
                entity_id=str(transfer["_id"]),
                old_value=transfer,
                new_value=completed
            )
        except Exception as e:
            logger.error(f"Failed to log audit action: {e}")

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