from app.repositories.order_repository import OrderRepository
from app.repositories.product_repository import ProductRepository
from app.services.warehouse_stock_service import WarehouseStockService
from fastapi import HTTPException, status


class OrderService:
    @classmethod
    async def place_order(cls, order_in, current_user: dict):
        user_role = current_user.get("role")
        if user_role != "viewer":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only viewers can place orders.",
            )
        processed_items = []
        total_price = 0
        user_id = str(current_user.get("id") or current_user.get("_id"))

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
                        product, item.variant_sku, item.warehouse_id, item.quantity
                    )
                )
            else:
                stock_reservation = await WarehouseStockService.reserve_stock(
                    product, item.variant_sku, item.quantity
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
            "customer_name": order_in.customer_name,
            "items": processed_items,
            "total_amount": total_price,
            "status": "pending",
            "user_details": {
                "name": current_user.get("name", "User"),
                "email": current_user.get("email"),
                "role": user_role,
            },
        }
        return await OrderRepository.create_order(order_dict)

    @classmethod
    async def confirm_order(cls, order_id: str, current_user: dict):

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
        return {"message": "Order successfully confirmed."}

    @classmethod
    async def cancel_order(cls, order_id: str):
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
                    product, sku, allocations
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
            )

        await OrderRepository.update_order_status(order_id, "cancelled")
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
