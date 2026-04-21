from typing import Optional
from datetime import datetime, timezone
from fastapi import HTTPException
import logging

from app.repositories.sales_order_repository import SalesOrderRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.warehouse_repository import WarehouseRepository
from app.repositories.variant_repository import VariantRepository
from app.models.sales_order import (
    SalesOrderStatus, VALID_TRANSITIONS,
    build_order_item, build_sales_order_document,
)
from app.schemas.sales_order import (
    SalesOrderCreateRequest, StatusUpdateRequest, ReturnRequest,
)
from app.repositories.inventory_movement_repository import InventoryMovementRepository
from app.models.inventory_movement import build_inventory_movement_document, MovementType

logger = logging.getLogger(__name__)


class SalesOrderService:
    def __init__(
        self,
        order_repo: SalesOrderRepository,
        product_repo: ProductRepository,
        warehouse_repo: WarehouseRepository,
        variant_repo: VariantRepository,
        movement_repo: InventoryMovementRepository = None,
    ):
        self.order_repo = order_repo
        self.product_repo = product_repo
        self.warehouse_repo = warehouse_repo
        self.variant_repo = variant_repo
        self.movement_repo = movement_repo

    # ── Create Order (Draft) ──────────────────────────────────────────────────

    async def create_order(
        self, payload: SalesOrderCreateRequest, customer: dict
    ) -> dict:
        # Validate warehouse exists and is active
        wh = await self.warehouse_repo.find_by_id(payload.warehouse_id)
        if not wh or not wh.get("is_active"):
            raise HTTPException(status_code=404, detail="Warehouse not found or inactive.")

        # Build line items — validate each product and price
        items = []
        for item in payload.items:
            product = await self.product_repo.find_by_id(item.product_id)
            if not product:
                raise HTTPException(
                    status_code=404,
                    detail=f"Product '{item.product_id}' not found."
                )
            if product["status"] not in ("active",):
                raise HTTPException(
                    status_code=400,
                    detail=f"Product '{product['name']}' is not available for ordering."
                )

            unit_price = product["selling_price"]
            variant_sku = None

            # If variant specified — use variant price
            if item.variant_id:
                variant = await self.variant_repo.find_by_variant_id(item.variant_id)
                if not variant or variant["product_id"] != item.product_id:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Variant '{item.variant_id}' not found on product '{product['name']}'."
                    )
                if not variant.get("is_active", True):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Variant '{variant['sku']}' is not active."
                    )
                unit_price = variant["selling_price"]
                variant_sku = variant["sku"]

            items.append(build_order_item(
                product_id=item.product_id,
                product_name=product["name"],
                sku=product["sku"],
                quantity=item.quantity,
                unit_price=unit_price,
                variant_id=item.variant_id,
                variant_sku=variant_sku,
                tax_percentage=product.get("tax_percentage", 0),
            ))

        shipping = payload.shipping_address.model_dump() if payload.shipping_address else {}
        doc = build_sales_order_document(
            customer_id=customer["_id"],
            customer_name=customer.get("full_name") or customer["username"],
            items=items,
            warehouse_id=payload.warehouse_id,
            created_by=customer["_id"],
            shipping_address=shipping,
            notes=payload.notes,
            discount=payload.discount_percentage,
        )
        created = await self.order_repo.create(doc)
        logger.info(f"Sales order {created['order_number']} created by {customer['_id']}")
        return created

    # ── Get / List ────────────────────────────────────────────────────────────

    async def get_order(self, order_id: str, requesting_user: dict) -> dict:
        order = await self.order_repo.find_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found.")
        # Customers can only see their own orders
        if (requesting_user["role"] == "customer"
                and order["customer_id"] != requesting_user["_id"]):
            raise HTTPException(status_code=403, detail="Access denied.")
        return order

    async def list_orders(
        self,
        requesting_user: dict,
        status: Optional[str],
        warehouse_id: Optional[str],
        search: Optional[str],
        page: int,
        page_size: int,
    ) -> dict:
        # Customers can only see their own orders
        customer_id = None
        if requesting_user["role"] == "customer":
            customer_id = requesting_user["_id"]

        skip = (page - 1) * page_size
        orders, total = await self.order_repo.list_orders(
            customer_id=customer_id,
            status=status,
            warehouse_id=warehouse_id,
            search=search,
            skip=skip,
            limit=page_size,
        )
        return {"total": total, "page": page, "page_size": page_size, "orders": orders}

    # ── Status Transition Engine ──────────────────────────────────────────────

    def _validate_transition(self, current: str, target: SalesOrderStatus):
        current_status = SalesOrderStatus(current)
        allowed = VALID_TRANSITIONS.get(current_status, [])
        if target not in allowed:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Cannot move order from '{current}' to '{target.value}'. "
                    f"Allowed next statuses: {[s.value for s in allowed]}"
                )
            )

    async def _record_status_change(
        self, order_id: str, new_status: SalesOrderStatus, changed_by: str, notes: str
    ):
        entry = {
            "status": new_status.value,
            "changed_by": changed_by,
            "timestamp": datetime.now(timezone.utc),
            "notes": notes,
        }
        await self.order_repo.push_status_history(order_id, entry)

    # ── Confirm Order — validates + reserves stock ────────────────────────────

    async def confirm_order(
        self, order_id: str, payload: StatusUpdateRequest, updated_by: str
    ) -> dict:
        order = await self.order_repo.find_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found.")

        self._validate_transition(order["status"], SalesOrderStatus.CONFIRMED)

        # ── Stock validation ──────────────────────────────────────────────────
        insufficient = []
        for item in order["items"]:
            stock_entry = await self.warehouse_repo.get_stock_entry(
                order["warehouse_id"], item["product_id"], item.get("variant_id")
            )
            available = stock_entry["quantity"] if stock_entry else 0
            if available < item["quantity"]:
                insufficient.append(
                    f"{item['product_name']} (SKU: {item['sku']}) — "
                    f"Available: {available}, Required: {item['quantity']}"
                )

        if insufficient:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for: {'; '.join(insufficient)}"
            )

        # ── Reserve stock (deduct from warehouse) ─────────────────────────────
        for item in order["items"]:
            await self.warehouse_repo.upsert_stock(
                warehouse_id=order["warehouse_id"],
                product_id=item["product_id"],
                variant_id=item.get("variant_id"),
                quantity_delta=-item["quantity"],
            )
            if self.movement_repo:
                doc = build_inventory_movement_document(
                    product_id=item["product_id"],
                    warehouse_id=order["warehouse_id"],
                    movement_type=MovementType.OUTWARD,
                    quantity=item["quantity"],
                    reference_type="SALES_ORDER",
                    reference_id=order_id,
                    performed_by=updated_by,
                    variant_id=item.get("variant_id"),
                    remarks=f"Order {order['order_number']} confirmed"
                )
                await self.movement_repo.create(doc)

        updated = await self.order_repo.update(order_id, {
            "status": SalesOrderStatus.CONFIRMED.value,
            "stock_reserved": True,
            "updated_by": updated_by,
        })
        await self._record_status_change(
            order_id, SalesOrderStatus.CONFIRMED, updated_by,
            payload.notes or "Order confirmed and stock reserved."
        )
        logger.info(f"Order {order['order_number']} confirmed by {updated_by}")
        return await self.order_repo.find_by_id(order_id)

    # ── Pack ──────────────────────────────────────────────────────────────────

    async def pack_order(
        self, order_id: str, payload: StatusUpdateRequest, updated_by: str
    ) -> dict:
        order = await self._get_and_validate_transition(
            order_id, SalesOrderStatus.PACKED
        )
        await self.order_repo.update(order_id, {
            "status": SalesOrderStatus.PACKED.value, "updated_by": updated_by
        })
        await self._record_status_change(
            order_id, SalesOrderStatus.PACKED, updated_by, payload.notes or "Order packed."
        )
        logger.info(f"Order {order['order_number']} packed by {updated_by}")
        return await self.order_repo.find_by_id(order_id)

    # Shipping

    async def ship_order(
        self, order_id: str, payload: StatusUpdateRequest, updated_by: str
    ) -> dict:
        order = await self._get_and_validate_transition(
            order_id, SalesOrderStatus.SHIPPED
        )
        await self.order_repo.update(order_id, {
            "status": SalesOrderStatus.SHIPPED.value, "updated_by": updated_by
        })
        await self._record_status_change(
            order_id, SalesOrderStatus.SHIPPED, updated_by, payload.notes or "Order dispatched."
        )
        logger.info(f"Order {order['order_number']} shipped by {updated_by}")
        return await self.order_repo.find_by_id(order_id)

    # Deliver 

    async def deliver_order(
        self, order_id: str, payload: StatusUpdateRequest, updated_by: str
    ) -> dict:
        order = await self._get_and_validate_transition(
            order_id, SalesOrderStatus.DELIVERED
        )
        await self.order_repo.update(order_id, {
            "status": SalesOrderStatus.DELIVERED.value, "updated_by": updated_by
        })
        await self._record_status_change(
            order_id, SalesOrderStatus.DELIVERED, updated_by,
            payload.notes or "Order delivered successfully."
        )
        logger.info(f"Order {order['order_number']} delivered by {updated_by}")
        return await self.order_repo.find_by_id(order_id)

    # Cancel 

    async def cancel_order(
        self, order_id: str, payload: StatusUpdateRequest, updated_by: str
    ) -> dict:
        order = await self._get_and_validate_transition(
            order_id, SalesOrderStatus.CANCELLED
        )
        # Release reserved stock back to warehouse
        if order.get("stock_reserved"):
            for item in order["items"]:
                await self.warehouse_repo.upsert_stock(
                    warehouse_id=order["warehouse_id"],
                    product_id=item["product_id"],
                    variant_id=item.get("variant_id"),
                    quantity_delta=item["quantity"],
                )
                if self.movement_repo:
                    doc = build_inventory_movement_document(
                        product_id=item["product_id"],
                        warehouse_id=order["warehouse_id"],
                        movement_type=MovementType.RETURN,
                        quantity=item["quantity"],
                        reference_type="SALES_ORDER_CANCELLED",
                        reference_id=order_id,
                        performed_by=updated_by,
                        variant_id=item.get("variant_id"),
                        remarks=f"Order {order['order_number']} cancelled"
                    )
                    await self.movement_repo.create(doc)

        await self.order_repo.update(order_id, {
            "status": SalesOrderStatus.CANCELLED.value,
            "stock_reserved": False,
            "updated_by": updated_by,
        })
        await self._record_status_change(
            order_id, SalesOrderStatus.CANCELLED, updated_by,
            payload.notes or "Order cancelled."
        )
        logger.info(f"Order {order['order_number']} cancelled by {updated_by}")
        return await self.order_repo.find_by_id(order_id)

    # Return 

    async def return_order(
        self, order_id: str, payload: ReturnRequest, updated_by: str
    ) -> dict:
        order = await self._get_and_validate_transition(
            order_id, SalesOrderStatus.RETURNED
        )
        # Restore stock for returned items
        items_to_restore = payload.items_to_return or [
            {"product_id": i["product_id"], "variant_id": i.get("variant_id"),
             "quantity": i["quantity"]}
            for i in order["items"]
        ]
        for item in items_to_restore:
            await self.warehouse_repo.upsert_stock(
                warehouse_id=order["warehouse_id"],
                product_id=item["product_id"] if isinstance(item, dict) else item.product_id,
                variant_id=item.get("variant_id") if isinstance(item, dict) else item.variant_id,
                quantity_delta=item["quantity"] if isinstance(item, dict) else item.quantity,
            )
            if self.movement_repo:
                pid = item["product_id"] if isinstance(item, dict) else item.product_id
                vid = item.get("variant_id") if isinstance(item, dict) else item.variant_id
                qty = item["quantity"] if isinstance(item, dict) else item.quantity
                doc = build_inventory_movement_document(
                    product_id=pid,
                    warehouse_id=order["warehouse_id"],
                    movement_type=MovementType.RETURN,
                    quantity=qty,
                    reference_type="SALES_ORDER_RETURNED",
                    reference_id=order_id,
                    performed_by=updated_by,
                    variant_id=vid,
                    remarks=f"Order {order['order_number']} returned. Reason: {payload.reason}"
                )
                await self.movement_repo.create(doc)

        await self.order_repo.update(order_id, {
            "status": SalesOrderStatus.RETURNED.value,
            "updated_by": updated_by,
            "return_reason": payload.reason,
        })
        await self._record_status_change(
            order_id, SalesOrderStatus.RETURNED, updated_by,
            f"Returned: {payload.reason}"
        )
        logger.info(f"Order {order['order_number']} returned. Reason: {payload.reason}")
        return await self.order_repo.find_by_id(order_id)

    # Order Summary 

    async def get_order_summary(self, customer_id: Optional[str] = None) -> dict:
        return await self.order_repo.get_order_summary(customer_id)

    # Helper 

    async def _get_and_validate_transition(
        self, order_id: str, target: SalesOrderStatus
    ) -> dict:
        order = await self.order_repo.find_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found.")
        self._validate_transition(order["status"], target)
        return order