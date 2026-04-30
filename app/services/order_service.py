from app.repositories.order_repository import OrderRepository
from app.repositories.product_repository import ProductRepository
from app.services.audit_service import AuditService
from app.services.warehouse_stock_service import WarehouseStockService
from app.utils.email_service import send_order_confirmation_email
from fastapi import HTTPException, status
import uuid
import re


class OrderService:
    @classmethod
    async def place_order(
        cls, order_in, current_user: dict, audit_context: dict | None = None
    ):
        user_role = current_user.get("role")
        if user_role != "viewer":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only viewers can place orders.",
            )

        customer_name = (
            order_in.customer_name or current_user.get("name") or "Customer"
        ).strip()
        customer_email = (
            (order_in.customer_email or current_user.get("email") or "").strip().lower()
        )
        shipping_address = (order_in.shipping_address or "").strip()
        raw_payment_method = getattr(
            order_in.payment_method, "value", order_in.payment_method
        )
        payment_method = str(raw_payment_method or "cod").strip().lower()

        if len(customer_name) < 2:
            raise HTTPException(status_code=400, detail="Customer name is required.")
        if customer_email and not re.match(
            r"^[^@\s]+@[^@\s]+\.[^@\s]+$", customer_email
        ):
            raise HTTPException(
                status_code=400, detail="Valid customer email is required."
            )
        if len(shipping_address) < 10:
            shipping_address = "Address will be confirmed with customer"
        if payment_method not in {"upi", "card", "netbanking", "cod"}:
            payment_method = "cod"

        processed_items = []
        total_price = 0
        user_id = str(current_user.get("id") or current_user.get("_id"))
        order_reference = f"SO-{uuid.uuid4().hex[:10].upper()}"

        for item in order_in.items:
            product = await ProductRepository.get_product_by_id(item.product_id)
            if not product:
                raise HTTPException(
                    status_code=404, detail=f"Product {item.product_id} not found"
                )

            price = product["selling_price"]
            display_name = product["name"]

            if item.variant_sku:
                variants = product.get("variants", [])
                variant = next(
                    (v for v in variants if v.get("sku") == item.variant_sku), None
                )

                if not variant:
                    raise HTTPException(
                        status_code=404, detail=f"Variant {item.variant_sku} not found"
                    )

                display_name = f"{product['name']} ({variant.get('name', 'Variant')})"
                price = variant.get("additional_price", price) or price

            if item.warehouse_id:
                stock_reservation = (
                    await WarehouseStockService.reserve_stock_from_selected_warehouse(
                        product,
                        item.variant_sku,
                        item.warehouse_id,
                        item.quantity,
                        performed_by=current_user,
                        reference_type="sales_order",
                        reference_id=order_reference,
                        remarks=f"Reserved for order {order_reference}",
                        audit_context=audit_context,
                    )
                )
            else:
                stock_reservation = await WarehouseStockService.reserve_stock(
                    product,
                    item.variant_sku,
                    item.quantity,
                    performed_by=current_user,
                    reference_type="sales_order",
                    reference_id=order_reference,
                    remarks=f"Reserved for order {order_reference}",
                    audit_context=audit_context,
                )

            if not item.variant_sku:
                display_name = product["name"]

            s_email = product.get("supplier_email")
            if not s_email and "supplier_details" in product:
                s_email = product["supplier_details"].get("email")

            item_total = price * item.quantity
            total_price += item_total

            processed_items.append(
                {
                    "product_id": item.product_id,
                    "variant_sku": item.variant_sku,
                    "warehouse_id": item.warehouse_id,
                    "name": display_name,
                    "quantity": item.quantity,
                    "price_at_purchase": price,
                    "supplier_email": s_email,
                    "warehouse_allocations": stock_reservation["warehouse_allocations"],
                }
            )

        order_dict = {
            "user_id": user_id,
            "customer_name": customer_name,
            "customer_email": customer_email or current_user.get("email"),
            "shipping_address": shipping_address,
            "payment_method": payment_method,
            "items": processed_items,
            "total_amount": total_price,
            "status": "pending",
            "order_reference": order_reference,
            "user_details": {
                "name": current_user.get("name", "User"),
                "email": current_user.get("email"),
                "role": user_role,
            },
        }
        saved_order = await OrderRepository.create_order(order_dict)

        email_sent, invoice_file_name, email_error = (
            await send_order_confirmation_email(saved_order)
        )
        if not email_sent and not email_error:
            email_error = "Email service is not configured on server"
        saved_order["confirmation_email_sent"] = email_sent
        saved_order["invoice_file_name"] = invoice_file_name
        saved_order["confirmation_email_error"] = email_error

        await AuditService.safe_log_action(
            user=current_user,
            action="order.create",
            entity_type="order",
            entity_id=saved_order["id"],
            old_value=None,
            new_value=saved_order,
            audit_context=audit_context,
        )

        return saved_order

    @classmethod
    async def confirm_order(
        cls, order_id: str, current_user: dict, audit_context: dict | None = None
    ):

        if current_user.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can confirm orders.",
            )

        order = await OrderRepository.get_order_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.get("status") != "pending":
            raise HTTPException(
                status_code=400,
                detail=f"Only 'pending' orders can be confirmed. Current status: {order.get('status')}",
            )

        await OrderRepository.update_order_status(order_id, "confirmed")
        await AuditService.safe_log_action(
            user=current_user,
            action="order.confirm",
            entity_type="order",
            entity_id=order_id,
            old_value=order,
            new_value={**order, "status": "confirmed"},
            audit_context=audit_context,
        )
        return {"message": "Order successfully confirmed."}

    @classmethod
    async def cancel_order(
        cls,
        order_id: str,
        current_user: dict | None = None,
        audit_context: dict | None = None,
    ):
        order = await OrderRepository.get_order_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.get("status") == "cancelled":
            raise HTTPException(status_code=400, detail="Order is already cancelled")

        for item in order.get("items", []):
            p_id = str(item["product_id"])
            sku = item.get("variant_sku")
            product = await ProductRepository.get_product_by_id(p_id)
            if not product:
                continue

            allocations = item.get("warehouse_allocations") or []
            if allocations:
                await WarehouseStockService.restore_stock_allocations(
                    product,
                    sku,
                    allocations,
                    performed_by=current_user
                    or {
                        "id": None,
                        "name": "Order System",
                        "email": None,
                        "role": "system",
                    },
                    reference_type="sales_order_cancellation",
                    reference_id=order.get("order_reference") or order_id,
                    remarks=f"Stock restored after cancellation of order {order_id}",
                    audit_context=audit_context,
                )
                continue

            await WarehouseStockService.restore_stock_allocations(
                product,
                sku,
                [
                    {
                        "warehouse_id": warehouse_stock.get("warehouse_id"),
                        "warehouse_name": warehouse_stock.get("warehouse_name"),
                        "quantity": item.get("quantity", 0),
                    }
                    for warehouse_stock in (
                        await WarehouseStockService.get_warehouse_candidates_for_restore(
                            product, sku
                        )
                    )[:1]
                ],
                performed_by=current_user
                or {
                    "id": None,
                    "name": "Order System",
                    "email": None,
                    "role": "system",
                },
                reference_type="sales_order_cancellation",
                reference_id=order.get("order_reference") or order_id,
                remarks=f"Stock restored after cancellation of order {order_id}",
                audit_context=audit_context,
            )

        await OrderRepository.update_order_status(order_id, "cancelled")
        await AuditService.safe_log_action(
            user=current_user
            or {
                "id": None,
                "name": "Order System",
                "email": None,
                "role": "system",
            },
            action="order.cancel",
            entity_type="order",
            entity_id=order_id,
            old_value=order,
            new_value={**order, "status": "cancelled"},
            audit_context=audit_context,
        )
        return {"message": "Order cancelled and stock restored successfully."}

    @classmethod
    async def get_orders_for_user(cls, user: dict):
        role = user.get("role")
        uid = str(user.get("id") or user.get("_id"))
        email = user.get("email")

        if role == "admin":
            return await OrderRepository.get_all_orders()
        if role == "supplier":
            return await OrderRepository.get_orders_by_supplier(email)
        return await OrderRepository.get_orders_by_user(uid)
