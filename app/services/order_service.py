from app.repositories.order_repository import OrderRepository
from app.repositories.product_repository import ProductRepository
from fastapi import HTTPException, status
from app.schemas.order import OrderCreate


class OrderService:
    @classmethod
    async def place_order(cls, order_in: OrderCreate, current_user: dict):

        user_role = current_user.get("role")
        if user_role in ["admin", "supplier"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Users with role '{user_role}' cannot place orders.",
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

            if product.get("reorder_level", 0) < item.quantity:
                raise HTTPException(
                    status_code=400, detail=f"Insufficient stock for {product['name']}"
                )

            s_email = product.get("supplier_email")
            if not s_email and "supplier_details" in product:
                s_email = product["supplier_details"].get("email")

            item_total = product["selling_price"] * item.quantity
            total_price += item_total

            processed_items.append(
                {
                    "product_id": item.product_id,
                    "name": product["name"],
                    "quantity": item.quantity,
                    "price_at_purchase": product["selling_price"],
                    "supplier_email": s_email,
                }
            )

            new_stock = product["reorder_level"] - item.quantity
            await ProductRepository.update_product(
                item.product_id, {"reorder_level": new_stock}
            )

        order_dict = {
            "user_id": user_id,
            "customer_name": order_in.customer_name,
            "items": processed_items,
            "total_amount": total_price,
            "status": "confirmed",
            "user_details": {
                "name": current_user.get("name", "User"),
                "email": current_user.get("email"),
                "role": user_role,
            },
        }
        return await OrderRepository.create_order(order_dict)

    @classmethod
    async def cancel_order(cls, order_id: str):

        order = await OrderRepository.get_order_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.get("status") == "cancelled":
            raise HTTPException(status_code=400, detail="Order is already cancelled")

        for item in order.get("items", []):
            p_id = str(item["product_id"])
            qty = item["quantity"]

            product = await ProductRepository.get_product_by_id(p_id)
            if product:
                restored_qty = product.get("reorder_level", 0) + qty
                await ProductRepository.update_product(
                    p_id, {"reorder_level": restored_qty}
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
