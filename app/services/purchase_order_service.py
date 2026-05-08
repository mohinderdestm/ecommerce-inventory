from datetime import datetime

from fastapi import HTTPException

from app.core.database import db
from app.models.purchase_order_model import purchase_order_model
from app.repositories.product_repository import ProductRepository
from app.repositories.purchase_order_repository import PurchaseOrderRepository
from app.services.audit_service import AuditService
from app.services.event_bus_service import EventBusService
from app.services.notification_service import NotificationService
from app.services.warehouse_stock_service import WarehouseStockService


class PurchaseOrderService:
    MANAGE_ROLES = {"admin", "manager"}
    VIEW_ROLES = {"admin", "manager", "supplier"}

    @staticmethod
    def _check_manage_access(user: dict):
        if user.get("role") not in PurchaseOrderService.MANAGE_ROLES:
            raise HTTPException(
                status_code=403,
                detail="Only admin and manager can manage purchase orders",
            )

    @staticmethod
    def _check_view_access(user: dict):
        if user.get("role") not in PurchaseOrderService.VIEW_ROLES:
            raise HTTPException(status_code=403, detail="Access denied")

    @staticmethod
    def _actor(user: dict):
        return {
            "id": user.get("id"),
            "name": user.get("name"),
            "email": user.get("email"),
            "role": user.get("role"),
        }

    @staticmethod
    def _generate_po_number():
        return f"PO-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    @staticmethod
    async def _resolve_supplier(supplier_email: str | None):
        if not supplier_email:
            return None

        supplier = await db["suppliers"].find_one({"email": supplier_email})
        if not supplier:
            raise HTTPException(status_code=404, detail="Supplier not found")
        return supplier

    @staticmethod
    def _resolve_variant(product: dict, variant_sku: str | None):
        if not variant_sku or variant_sku == product.get("sku"):
            return product.get("sku"), "Base Product"

        for variant in product.get("variants", []):
            if variant.get("sku") == variant_sku:
                return variant_sku, variant.get("name", "Variant")

        raise HTTPException(
            status_code=404, detail=f"Variant SKU {variant_sku} not found"
        )

    @staticmethod
    async def _normalize_item(item):
        product = await ProductRepository.get_product_by_id(item.product_id)
        if not product:
            raise HTTPException(
                status_code=404, detail=f"Product {item.product_id} not found"
            )

        variant_sku, variant_name = PurchaseOrderService._resolve_variant(
            product, item.variant_sku
        )
        return {
            "product_id": product["id"],
            "product_name": product.get("name"),
            "variant_sku": variant_sku,
            "variant_name": variant_name,
            "ordered_quantity": int(item.quantity),
            "received_quantity": 0,
            "unit_cost": float(item.unit_cost or 0),
            "remarks": item.remarks,
        }

    @staticmethod
    async def create_draft(data, user: dict, audit_context: dict | None = None):
        PurchaseOrderService._check_manage_access(user)

        supplier = await PurchaseOrderService._resolve_supplier(data.supplier_email)
        po_number = PurchaseOrderService._generate_po_number()

        existing_number = await PurchaseOrderRepository.get_purchase_order_by_number(
            po_number
        )
        if existing_number:
            po_number = f"{po_number}-{user.get('id', 'SYS')[-4:]}"

        normalized_items = []
        for item in data.items:
            normalized_items.append(await PurchaseOrderService._normalize_item(item))

        po_doc = {
            "po_number": po_number,
            "supplier_email": data.supplier_email,
            "supplier_name": supplier.get("name") if supplier else None,
            "status": "draft",
            "items": normalized_items,
            "invoice_metadata": {},
            "receipts": [],
            "notes": data.notes,
            "created_by": PurchaseOrderService._actor(user),
            "approved_by": None,
            "rejected_by": None,
            "submitted_at": None,
            "approved_at": None,
            "rejected_at": None,
            "received_at": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        po_id = await PurchaseOrderRepository.create_purchase_order(po_doc)
        created = await PurchaseOrderRepository.get_purchase_order_by_id(po_id)
        await AuditService.safe_log_action(
            user=user,
            action="purchase_order.create",
            entity_type="purchase_order",
            entity_id=po_id,
            old_value=None,
            new_value=created,
            audit_context=audit_context,
        )
        created_model = purchase_order_model(created)
        await EventBusService.publish(
            topic_key="purchase_orders.events",
            event_type="purchase_order.created",
            aggregate_type="purchase_order",
            aggregate_id=po_id,
            payload=created_model,
            user=user,
        )
        return created_model

    @staticmethod
    async def _get_accessible_po(po_id: str, user: dict):
        po = await PurchaseOrderRepository.get_purchase_order_by_id(po_id)
        if not po:
            raise HTTPException(status_code=404, detail="Purchase order not found")

        role = user.get("role")
        if role == "supplier" and po.get("supplier_email") != user.get("email"):
            raise HTTPException(
                status_code=403, detail="Access denied for this purchase order"
            )

        return po

    @staticmethod
    async def list_purchase_orders(
        user: dict, status: str | None = None, limit: int = 200
    ):
        PurchaseOrderService._check_view_access(user)

        supplier_email = None
        if user.get("role") == "supplier":
            supplier_email = user.get("email")

        rows = await PurchaseOrderRepository.list_purchase_orders(
            status=status,
            supplier_email=supplier_email,
            limit=limit,
        )
        return [purchase_order_model(row) for row in rows]

    @staticmethod
    async def get_purchase_order(po_id: str, user: dict):
        PurchaseOrderService._check_view_access(user)
        po = await PurchaseOrderService._get_accessible_po(po_id, user)
        return purchase_order_model(po)

    @staticmethod
    async def add_items(
        po_id: str, data, user: dict, audit_context: dict | None = None
    ):
        PurchaseOrderService._check_manage_access(user)
        po = await PurchaseOrderService._get_accessible_po(po_id, user)

        if po.get("status") != "draft":
            raise HTTPException(
                status_code=400,
                detail="Items can only be added to draft purchase orders",
            )

        items = po.get("items", [])
        for item in data.items:
            items.append(await PurchaseOrderService._normalize_item(item))

        await PurchaseOrderRepository.replace_items(po_id, items)
        updated = await PurchaseOrderRepository.get_purchase_order_by_id(po_id)
        await AuditService.safe_log_action(
            user=user,
            action="purchase_order.add_items",
            entity_type="purchase_order",
            entity_id=po_id,
            old_value=po,
            new_value=updated,
            audit_context=audit_context,
        )
        updated_model = purchase_order_model(updated)
        await EventBusService.publish(
            topic_key="purchase_orders.events",
            event_type="purchase_order.items_added",
            aggregate_type="purchase_order",
            aggregate_id=po_id,
            payload=updated_model,
            user=user,
        )
        return updated_model

    @staticmethod
    async def submit(
        po_id: str,
        user: dict,
        remarks: str | None = None,
        audit_context: dict | None = None,
    ):
        PurchaseOrderService._check_manage_access(user)
        po = await PurchaseOrderService._get_accessible_po(po_id, user)

        if po.get("status") != "draft":
            raise HTTPException(
                status_code=400, detail="Only draft purchase orders can be submitted"
            )
        if not po.get("items"):
            raise HTTPException(
                status_code=400, detail="Add at least one item before submitting"
            )

        await PurchaseOrderRepository.update_fields(
            po_id,
            {
                "status": "submitted",
                "submitted_at": datetime.utcnow(),
                "notes": remarks or po.get("notes"),
            },
        )

        updated = await PurchaseOrderRepository.get_purchase_order_by_id(po_id)
        await AuditService.safe_log_action(
            user=user,
            action="purchase_order.submit",
            entity_type="purchase_order",
            entity_id=po_id,
            old_value=po,
            new_value=updated,
            audit_context=audit_context,
        )
        await NotificationService.dispatch_system_notification(
            type="purchase_order_submitted",
            title=f"Purchase Order Submitted: {updated.get('po_number')}",
            message=f"Purchase order {updated.get('po_number')} is submitted and pending approval.",
            severity="info",
            target_roles=["admin", "manager"],
            reference_type="purchase_order",
            reference_id=str(updated.get("_id")),
            dedupe_key=f"po_submitted:{updated.get('_id')}",
            metadata={"status": "submitted"},
        )
        updated_model = purchase_order_model(updated)
        await EventBusService.publish(
            topic_key="purchase_orders.events",
            event_type="purchase_order.submitted",
            aggregate_type="purchase_order",
            aggregate_id=po_id,
            payload=updated_model,
            user=user,
        )
        return updated_model

    @staticmethod
    async def approve(
        po_id: str,
        user: dict,
        remarks: str | None = None,
        audit_context: dict | None = None,
    ):
        PurchaseOrderService._check_manage_access(user)
        po = await PurchaseOrderService._get_accessible_po(po_id, user)

        if po.get("status") != "submitted":
            raise HTTPException(
                status_code=400, detail="Only submitted purchase orders can be approved"
            )

        await PurchaseOrderRepository.update_fields(
            po_id,
            {
                "status": "approved",
                "approved_by": PurchaseOrderService._actor(user),
                "approved_at": datetime.utcnow(),
                "notes": remarks or po.get("notes"),
            },
        )
        updated = await PurchaseOrderRepository.get_purchase_order_by_id(po_id)
        await AuditService.safe_log_action(
            user=user,
            action="purchase_order.approve",
            entity_type="purchase_order",
            entity_id=po_id,
            old_value=po,
            new_value=updated,
            audit_context=audit_context,
        )
        await NotificationService.dispatch_system_notification(
            type="purchase_order_approved",
            title=f"Purchase Order Approved: {updated.get('po_number')}",
            message=f"Purchase order {updated.get('po_number')} is approved and ready for receiving.",
            severity="info",
            target_roles=["admin", "manager"],
            target_users=(
                [updated.get("supplier_email")] if updated.get("supplier_email") else []
            ),
            reference_type="purchase_order",
            reference_id=str(updated.get("_id")),
            dedupe_key=f"po_approved:{updated.get('_id')}",
            metadata={"status": "approved"},
        )
        updated_model = purchase_order_model(updated)
        await EventBusService.publish(
            topic_key="purchase_orders.events",
            event_type="purchase_order.approved",
            aggregate_type="purchase_order",
            aggregate_id=po_id,
            payload=updated_model,
            user=user,
        )
        return updated_model

    @staticmethod
    async def reject(
        po_id: str,
        user: dict,
        remarks: str | None = None,
        audit_context: dict | None = None,
    ):
        PurchaseOrderService._check_manage_access(user)
        po = await PurchaseOrderService._get_accessible_po(po_id, user)

        if po.get("status") != "submitted":
            raise HTTPException(
                status_code=400, detail="Only submitted purchase orders can be rejected"
            )

        await PurchaseOrderRepository.update_fields(
            po_id,
            {
                "status": "rejected",
                "rejected_by": PurchaseOrderService._actor(user),
                "rejected_at": datetime.utcnow(),
                "notes": remarks or po.get("notes"),
            },
        )
        updated = await PurchaseOrderRepository.get_purchase_order_by_id(po_id)
        await AuditService.safe_log_action(
            user=user,
            action="purchase_order.reject",
            entity_type="purchase_order",
            entity_id=po_id,
            old_value=po,
            new_value=updated,
            audit_context=audit_context,
        )
        await NotificationService.dispatch_system_notification(
            type="purchase_order_rejected",
            title=f"Purchase Order Rejected: {updated.get('po_number')}",
            message=f"Purchase order {updated.get('po_number')} has been rejected.",
            severity="warning",
            target_roles=["admin", "manager"],
            target_users=(
                [updated.get("supplier_email")] if updated.get("supplier_email") else []
            ),
            reference_type="purchase_order",
            reference_id=str(updated.get("_id")),
            dedupe_key=f"po_rejected:{updated.get('_id')}",
            metadata={"status": "rejected"},
        )
        updated_model = purchase_order_model(updated)
        await EventBusService.publish(
            topic_key="purchase_orders.events",
            event_type="purchase_order.rejected",
            aggregate_type="purchase_order",
            aggregate_id=po_id,
            payload=updated_model,
            user=user,
        )
        return updated_model

    @staticmethod
    async def cancel(
        po_id: str,
        user: dict,
        remarks: str | None = None,
        audit_context: dict | None = None,
    ):
        PurchaseOrderService._check_manage_access(user)
        po = await PurchaseOrderService._get_accessible_po(po_id, user)

        if po.get("status") in {"completed", "cancelled"}:
            raise HTTPException(
                status_code=400, detail=f"Purchase order already {po.get('status')}"
            )

        await PurchaseOrderRepository.update_fields(
            po_id,
            {
                "status": "cancelled",
                "notes": remarks or po.get("notes"),
            },
        )
        updated = await PurchaseOrderRepository.get_purchase_order_by_id(po_id)
        await AuditService.safe_log_action(
            user=user,
            action="purchase_order.cancel",
            entity_type="purchase_order",
            entity_id=po_id,
            old_value=po,
            new_value=updated,
            audit_context=audit_context,
        )
        updated_model = purchase_order_model(updated)
        await EventBusService.publish(
            topic_key="purchase_orders.events",
            event_type="purchase_order.cancelled",
            aggregate_type="purchase_order",
            aggregate_id=po_id,
            payload=updated_model,
            user=user,
        )
        return updated_model

    @staticmethod
    async def update_invoice_metadata(
        po_id: str, data, user: dict, audit_context: dict | None = None
    ):
        PurchaseOrderService._check_manage_access(user)
        po = await PurchaseOrderService._get_accessible_po(po_id, user)

        invoice_payload = {
            key: value.isoformat() if hasattr(value, "isoformat") and value else value
            for key, value in data.dict(exclude_none=True).items()
        }
        merged = {**(po.get("invoice_metadata") or {}), **invoice_payload}

        await PurchaseOrderRepository.update_fields(po_id, {"invoice_metadata": merged})
        updated = await PurchaseOrderRepository.get_purchase_order_by_id(po_id)
        await AuditService.safe_log_action(
            user=user,
            action="purchase_order.update_invoice",
            entity_type="purchase_order",
            entity_id=po_id,
            old_value=po,
            new_value=updated,
            audit_context=audit_context,
        )
        updated_model = purchase_order_model(updated)
        await EventBusService.publish(
            topic_key="purchase_orders.events",
            event_type="purchase_order.invoice_updated",
            aggregate_type="purchase_order",
            aggregate_id=po_id,
            payload=updated_model,
            user=user,
        )
        return updated_model

    @staticmethod
    async def _apply_expiry(product: dict, variant_sku: str | None, expiry_date: str):
        if not expiry_date:
            return

        if not variant_sku or variant_sku == product.get("sku"):
            await ProductRepository.update_product(
                product["id"], {"expiry_date": expiry_date}
            )
            return

        variants = []
        for variant in product.get("variants", []):
            v = dict(variant)
            if v.get("sku") == variant_sku:
                v["expiry_date"] = expiry_date
            variants.append(v)
        await ProductRepository.update_product(product["id"], {"variants": variants})

    @staticmethod
    async def receive(po_id: str, data, user: dict, audit_context: dict | None = None):
        PurchaseOrderService._check_manage_access(user)
        po = await PurchaseOrderService._get_accessible_po(po_id, user)

        if po.get("status") not in {"approved", "partially_received"}:
            raise HTTPException(
                status_code=400,
                detail="Only approved or partially received purchase orders can be received",
            )
        if not data.lines:
            raise HTTPException(
                status_code=422, detail="At least one receipt line is required"
            )

        items = po.get("items", [])
        receipts = po.get("receipts", [])

        for line in data.lines:
            matching_item = None
            for item in items:
                same_product = item.get("product_id") == line.product_id
                same_variant = (item.get("variant_sku") or "") == (
                    line.variant_sku or ""
                )
                if not line.variant_sku and item.get("variant_name") == "Base Product":
                    same_variant = True
                if same_product and same_variant:
                    matching_item = item
                    break

            if not matching_item:
                raise HTTPException(
                    status_code=404,
                    detail=f"Receipt line item not found in purchase order: {line.product_id}",
                )

            pending_qty = int(matching_item.get("ordered_quantity") or 0) - int(
                matching_item.get("received_quantity") or 0
            )
            if pending_qty <= 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"No pending quantity for product {matching_item.get('product_name')}",
                )
            if line.quantity_received > pending_qty:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Received quantity exceeds pending quantity for "
                        f"{matching_item.get('product_name')}. Pending: {pending_qty}"
                    ),
                )

            product = await ProductRepository.get_product_by_id(line.product_id)
            if not product:
                raise HTTPException(
                    status_code=404, detail=f"Product {line.product_id} not found"
                )

            final_sku, variant_name = PurchaseOrderService._resolve_variant(
                product, line.variant_sku
            )

            await WarehouseStockService.assign_stock_entry(
                warehouse_id=line.warehouse_id,
                product=product,
                variant_sku=final_sku,
                quantity=int(line.quantity_received),
                variant_name=variant_name,
                performed_by=user,
                reference_type="purchase_order",
                reference_id=po.get("po_number"),
                remarks=line.remarks or f"PO Receipt {po.get('po_number')}",
                movement_type="inward",
                audit_context=audit_context,
            )

            if line.expiry_date:
                await PurchaseOrderService._apply_expiry(
                    product,
                    line.variant_sku,
                    line.expiry_date.isoformat(),
                )

            matching_item["received_quantity"] = int(
                matching_item.get("received_quantity") or 0
            ) + int(line.quantity_received)

            receipts.append(
                {
                    "product_id": line.product_id,
                    "variant_sku": line.variant_sku,
                    "warehouse_id": line.warehouse_id,
                    "quantity_received": int(line.quantity_received),
                    "remarks": line.remarks,
                    "expiry_date": (
                        line.expiry_date.isoformat() if line.expiry_date else None
                    ),
                    "received_by": PurchaseOrderService._actor(user),
                    "received_at": datetime.utcnow(),
                }
            )

        all_received = all(
            int(item.get("received_quantity") or 0)
            >= int(item.get("ordered_quantity") or 0)
            for item in items
        )
        new_status = "completed" if all_received else "partially_received"

        update_fields = {
            "items": items,
            "receipts": receipts,
            "status": new_status,
            "received_at": datetime.utcnow() if all_received else po.get("received_at"),
        }

        if data.invoice_metadata:
            invoice_payload = {
                key: (
                    value.isoformat()
                    if hasattr(value, "isoformat") and value
                    else value
                )
                for key, value in data.invoice_metadata.dict(exclude_none=True).items()
            }
            update_fields["invoice_metadata"] = {
                **(po.get("invoice_metadata") or {}),
                **invoice_payload,
            }

        await PurchaseOrderRepository.update_fields(po_id, update_fields)
        updated = await PurchaseOrderRepository.get_purchase_order_by_id(po_id)
        await AuditService.safe_log_action(
            user=user,
            action="purchase_order.receive",
            entity_type="purchase_order",
            entity_id=po_id,
            old_value=po,
            new_value=updated,
            audit_context=audit_context,
        )

        await NotificationService.dispatch_system_notification(
            type="purchase_order_received",
            title=f"Purchase Order {updated.get('po_number')} {new_status.replace('_', ' ').title()}",
            message=(
                f"Purchase order {updated.get('po_number')} has been marked as "
                f"{new_status.replace('_', ' ')}."
            ),
            severity="info",
            target_roles=["admin", "manager"],
            target_users=(
                [updated.get("supplier_email")] if updated.get("supplier_email") else []
            ),
            reference_type="purchase_order",
            reference_id=str(updated.get("_id")),
            dedupe_key=f"po_receive:{updated.get('_id')}:{new_status}",
            metadata={"status": new_status},
        )

        updated_model = purchase_order_model(updated)
        await EventBusService.publish(
            topic_key="purchase_orders.events",
            event_type="purchase_order.received",
            aggregate_type="purchase_order",
            aggregate_id=po_id,
            payload=updated_model,
            metadata={"status": new_status},
            user=user,
        )

        return updated_model
