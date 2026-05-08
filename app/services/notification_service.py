from datetime import datetime, timedelta, date
from typing import Optional
from uuid import uuid4

from app.core.database import db
from app.core.kafka import kafka_manager
from app.models.notification_model import notification_model
from app.repositories.notification_repository import NotificationRepository
from app.services.event_bus_service import EventBusService
from app.repositories.product_repository import ProductRepository
from app.services.product_service import ProductService


class NotificationService:
    @staticmethod
    def _parse_date(value) -> Optional[date]:
        if not value:
            return None
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        if isinstance(value, datetime):
            return value.date()
        try:
            normalized = str(value).replace("Z", "+00:00")
            return datetime.fromisoformat(normalized).date()
        except Exception:
            return None

    @staticmethod
    async def create_system_notification(
        *,
        type: str,
        title: str,
        message: str,
        severity: str = "info",
        target_roles: Optional[list[str]] = None,
        target_users: Optional[list[str]] = None,
        reference_type: Optional[str] = None,
        reference_id: Optional[str] = None,
        dedupe_key: Optional[str] = None,
        metadata: Optional[dict] = None,
        channels: Optional[list[str]] = None,
    ):
        if dedupe_key:
            existing = await NotificationRepository.find_active_by_dedupe_key(
                dedupe_key
            )
            if existing:
                return notification_model(existing)

        now = datetime.utcnow()
        payload = {
            "type": type,
            "title": title,
            "message": message,
            "severity": severity,
            "target_roles": target_roles or ["admin", "manager"],
            "target_users": target_users or [],
            "reference_type": reference_type,
            "reference_id": reference_id,
            "metadata": metadata or {},
            "channels": channels or ["in_app", "email_simulation"],
            "email_simulation": {
                "subject": title,
                "body": message,
                "sent_at": now,
                "to_roles": target_roles or ["admin", "manager"],
                "to_users": target_users or [],
            },
            "dedupe_key": dedupe_key,
            "is_read": False,
            "read_at": None,
            "created_at": now,
            "updated_at": now,
        }

        notification_id = await NotificationRepository.create(payload)
        created = await NotificationRepository.get_by_id(notification_id)
        created_model = notification_model(created)
        await EventBusService.publish(
            topic_key="notifications.events",
            event_type="notification.created",
            aggregate_type="notification",
            aggregate_id=created_model["id"],
            payload=created_model,
            metadata={"delivery_mode": "direct"},
        )
        return created_model

    @staticmethod
    async def dispatch_system_notification(
        *,
        type: str,
        title: str,
        message: str,
        severity: str = "info",
        target_roles: Optional[list[str]] = None,
        target_users: Optional[list[str]] = None,
        reference_type: Optional[str] = None,
        reference_id: Optional[str] = None,
        dedupe_key: Optional[str] = None,
        metadata: Optional[dict] = None,
        channels: Optional[list[str]] = None,
    ):
        payload = {
            "type": type,
            "title": title,
            "message": message,
            "severity": severity,
            "target_roles": target_roles,
            "target_users": target_users,
            "reference_type": reference_type,
            "reference_id": reference_id,
            "dedupe_key": dedupe_key,
            "metadata": metadata,
            "channels": channels,
        }
        command = {
            "command_id": uuid4().hex,
            "command_type": "notification.create",
            "issued_at": datetime.utcnow().isoformat(),
            "payload": payload,
        }

        published = await kafka_manager.publish(
            kafka_manager.topic("notifications.commands"),
            command,
            key=dedupe_key or reference_id or type,
        )
        if published:
            return {"queued": True, "transport": "kafka"}

        created = await NotificationService.create_system_notification(**payload)
        return {"queued": False, "transport": "direct", "notification": created}

    @staticmethod
    async def _refresh_low_stock_alerts():
        products = await ProductRepository.get_all_products()
        enriched = await ProductService._attach_warehouse_stock(products)

        for product in enriched:
            product_stock = int(product.get("stock") or 0)
            threshold = int(product.get("low_stock_threshold") or 5)
            supplier_email = product.get("supplier_email")

            if product_stock <= threshold:
                await NotificationService.create_system_notification(
                    type="low_stock",
                    title=f"Low Stock: {product.get('name')}",
                    message=(
                        f"{product.get('name')} stock is {product_stock}, "
                        f"which is at or below threshold {threshold}."
                    ),
                    severity="warning",
                    target_roles=["admin", "manager"],
                    target_users=[supplier_email] if supplier_email else [],
                    reference_type="product",
                    reference_id=product.get("id"),
                    dedupe_key=f"low_stock:{product.get('id')}:{product.get('sku')}",
                    metadata={
                        "product_id": product.get("id"),
                        "sku": product.get("sku"),
                        "current_stock": product_stock,
                        "threshold": threshold,
                        "impact": "reorder_recommended",
                    },
                )

            for variant in product.get("variants", []):
                variant_stock = int(variant.get("stock") or 0)
                variant_threshold = int(
                    variant.get("low_stock_threshold")
                    if variant.get("low_stock_threshold") is not None
                    else threshold
                )
                if variant_stock <= variant_threshold:
                    await NotificationService.create_system_notification(
                        type="low_stock",
                        title=f"Low Stock: {product.get('name')} ({variant.get('name')})",
                        message=(
                            f"{product.get('name')} ({variant.get('name')}) stock is {variant_stock}, "
                            f"which is at or below threshold {variant_threshold}."
                        ),
                        severity="warning",
                        target_roles=["admin", "manager"],
                        target_users=[supplier_email] if supplier_email else [],
                        reference_type="product_variant",
                        reference_id=product.get("id"),
                        dedupe_key=f"low_stock:{product.get('id')}:{variant.get('sku')}",
                        metadata={
                            "product_id": product.get("id"),
                            "variant_sku": variant.get("sku"),
                            "current_stock": variant_stock,
                            "threshold": variant_threshold,
                            "impact": "variant_reorder_recommended",
                        },
                    )

    @staticmethod
    async def _refresh_expiry_alerts():
        today = datetime.utcnow().date()
        expiry_window = today + timedelta(days=7)
        products = await ProductRepository.get_all_products()
        enriched = await ProductService._attach_warehouse_stock(products)

        for product in enriched:
            supplier_email = product.get("supplier_email")

            product_expiry = NotificationService._parse_date(product.get("expiry_date"))
            if (
                product_expiry
                and int(product.get("base_stock") or 0) > 0
                and product_expiry <= expiry_window
            ):
                expired = product_expiry < today
                await NotificationService.create_system_notification(
                    type="expiry",
                    title=f"{'Expired' if expired else 'Expiring Soon'}: {product.get('name')}",
                    message=(
                        f"{product.get('name')} has expiry date {product_expiry.isoformat()} "
                        f"and current stock {int(product.get('base_stock') or 0)}."
                    ),
                    severity="critical" if expired else "warning",
                    target_roles=["admin", "manager"],
                    target_users=[supplier_email] if supplier_email else [],
                    reference_type="product",
                    reference_id=product.get("id"),
                    dedupe_key=f"expiry:{product.get('id')}:{product_expiry.isoformat()}",
                    metadata={
                        "product_id": product.get("id"),
                        "expiry_date": product_expiry.isoformat(),
                        "impact": (
                            "immediate_action_required" if expired else "expiring_soon"
                        ),
                    },
                )

            for variant in product.get("variants", []):
                variant_expiry = NotificationService._parse_date(
                    variant.get("expiry_date")
                )
                variant_stock = int(variant.get("stock") or 0)
                if (
                    variant_expiry
                    and variant_stock > 0
                    and variant_expiry <= expiry_window
                ):
                    expired = variant_expiry < today
                    await NotificationService.create_system_notification(
                        type="expiry",
                        title=(
                            f"{'Expired' if expired else 'Expiring Soon'}: "
                            f"{product.get('name')} ({variant.get('name')})"
                        ),
                        message=(
                            f"{product.get('name')} ({variant.get('name')}) has expiry date "
                            f"{variant_expiry.isoformat()} and current stock {variant_stock}."
                        ),
                        severity="critical" if expired else "warning",
                        target_roles=["admin", "manager"],
                        target_users=[supplier_email] if supplier_email else [],
                        reference_type="product_variant",
                        reference_id=product.get("id"),
                        dedupe_key=(
                            f"expiry:{product.get('id')}:{variant.get('sku')}:"
                            f"{variant_expiry.isoformat()}"
                        ),
                        metadata={
                            "product_id": product.get("id"),
                            "variant_sku": variant.get("sku"),
                            "expiry_date": variant_expiry.isoformat(),
                            "impact": (
                                "immediate_action_required"
                                if expired
                                else "expiring_soon"
                            ),
                        },
                    )

    @staticmethod
    async def _refresh_delayed_po_alerts():
        cutoff = datetime.utcnow() - timedelta(hours=48)
        delayed_orders = (
            await db["purchase_orders"]
            .find(
                {
                    "status": {"$in": ["submitted", "approved", "partially_received"]},
                    "updated_at": {"$lte": cutoff},
                }
            )
            .to_list(length=None)
        )

        for po in delayed_orders:
            po_number = po.get("po_number")
            await NotificationService.create_system_notification(
                type="delayed_purchase_order",
                title=f"Delayed Purchase Order: {po_number}",
                message=f"Purchase order {po_number} is delayed and still in {po.get('status')} status.",
                severity="warning",
                target_roles=["admin", "manager"],
                target_users=(
                    [po.get("supplier_email")] if po.get("supplier_email") else []
                ),
                reference_type="purchase_order",
                reference_id=str(po.get("_id")),
                dedupe_key=f"po_delayed:{po.get('_id')}:{po.get('status')}",
                metadata={
                    "status": po.get("status"),
                    "po_number": po_number,
                    "impact": "follow_up_with_supplier",
                },
            )

    @staticmethod
    async def _refresh_unfulfilled_sales_order_alerts():
        cutoff = datetime.utcnow() - timedelta(hours=24)
        delayed_sales_orders = (
            await db["orders"]
            .find({"status": "pending", "created_at": {"$lte": cutoff}})
            .to_list(length=None)
        )

        for order in delayed_sales_orders:
            order_id = str(order.get("_id"))
            await NotificationService.create_system_notification(
                type="unfulfilled_sales_order",
                title=f"Unfulfilled Sales Order: {order_id[-6:].upper()}",
                message=(
                    f"Sales order {order_id} for customer {order.get('customer_name')} "
                    "is still pending fulfillment."
                ),
                severity="warning",
                target_roles=["admin", "manager"],
                reference_type="sales_order",
                reference_id=order_id,
                dedupe_key=f"sales_order_pending:{order_id}",
                metadata={
                    "order_id": order_id,
                    "customer_name": order.get("customer_name"),
                    "impact": "fulfillment_required",
                },
            )

    @staticmethod
    async def _refresh_viewer_notifications(user: dict):
        email = user.get("email")
        if not email:
            return

        pending_cutoff = datetime.utcnow() - timedelta(hours=2)
        pending_orders = (
            await db["orders"]
            .find(
                {
                    "user_details.email": email,
                    "status": "pending",
                    "created_at": {"$lte": pending_cutoff},
                }
            )
            .to_list(length=20)
        )

        for order in pending_orders:
            order_id = str(order.get("_id"))
            await NotificationService.create_system_notification(
                type="viewer_order_pending",
                title="Order Awaiting Confirmation",
                message=(
                    f"Your order #{order_id[-6:].upper()} is still pending. "
                    "Our team is processing it."
                ),
                severity="warning",
                target_users=[email],
                reference_type="sales_order",
                reference_id=order_id,
                dedupe_key=f"viewer_pending:{order_id}",
                metadata={"impact": "track_order", "order_id": order_id},
            )

        recent_cutoff = datetime.utcnow() - timedelta(days=7)
        updated_orders = (
            await db["orders"]
            .find(
                {
                    "user_details.email": email,
                    "status": {"$in": ["confirmed", "cancelled"]},
                    "created_at": {"$gte": recent_cutoff},
                }
            )
            .to_list(length=40)
        )

        for order in updated_orders:
            order_id = str(order.get("_id"))
            status = order.get("status")
            await NotificationService.create_system_notification(
                type="viewer_order_status",
                title=f"Order {status.title()}",
                message=(
                    f"Your order #{order_id[-6:].upper()} has been {status}. "
                    "Open order details for more information."
                ),
                severity="info" if status == "confirmed" else "warning",
                target_users=[email],
                reference_type="sales_order",
                reference_id=order_id,
                dedupe_key=f"viewer_status:{order_id}:{status}",
                metadata={
                    "impact": "open_order_details",
                    "order_id": order_id,
                    "status": status,
                },
            )

    @staticmethod
    async def _refresh_supplier_notifications(user: dict):
        email = user.get("email")
        if not email:
            return

        supplier_pos = (
            await db["purchase_orders"]
            .find(
                {
                    "supplier_email": email,
                    "status": {"$in": ["submitted", "approved", "partially_received"]},
                }
            )
            .to_list(length=50)
        )

        for po in supplier_pos:
            po_id = str(po.get("_id"))
            status = po.get("status")
            severity = "info"
            impact = "review_purchase_order"
            if status == "approved":
                severity = "warning"
                impact = "prepare_supply_and_invoice"
            elif status == "partially_received":
                severity = "warning"
                impact = "complete_remaining_supply"

            await NotificationService.create_system_notification(
                type="supplier_po_update",
                title=f"PO Update: {po.get('po_number')}",
                message=(
                    f"Purchase order {po.get('po_number')} is currently {status.replace('_', ' ')}. "
                    "Please review and take the next action."
                ),
                severity=severity,
                target_users=[email],
                reference_type="purchase_order",
                reference_id=po_id,
                dedupe_key=f"supplier_po:{po_id}:{status}",
                metadata={
                    "impact": impact,
                    "po_number": po.get("po_number"),
                    "status": status,
                },
            )

    @staticmethod
    async def _refresh_manager_admin_brief(user: dict):
        role = user.get("role")
        email = user.get("email")
        if role not in {"admin", "manager"}:
            return

        now = datetime.utcnow()
        window_24h = now - timedelta(hours=24)
        pending_sales = await db["orders"].count_documents({"status": "pending"})
        delayed_pos = await db["purchase_orders"].count_documents(
            {
                "status": {"$in": ["submitted", "approved", "partially_received"]},
                "updated_at": {"$lte": now - timedelta(hours=48)},
            }
        )
        new_orders = await db["orders"].count_documents(
            {"created_at": {"$gte": window_24h}}
        )

        await NotificationService.create_system_notification(
            type="operations_brief",
            title="Operations Brief",
            message=(
                f"Pending sales orders: {pending_sales}. "
                f"Delayed purchase orders: {delayed_pos}. "
                f"New orders (24h): {new_orders}."
            ),
            severity="info",
            target_users=[email] if email else [],
            target_roles=[role],
            reference_type="operations_dashboard",
            reference_id=now.strftime("%Y-%m-%d"),
            dedupe_key=f"ops_brief:{role}:{now.strftime('%Y-%m-%d')}",
            metadata={
                "impact": "review_dashboard",
                "pending_sales_orders": pending_sales,
                "delayed_purchase_orders": delayed_pos,
                "new_orders_24h": new_orders,
            },
        )

    @staticmethod
    async def _refresh_role_specific_alerts(user: dict):
        role = user.get("role", "viewer")
        if role == "viewer":
            await NotificationService._refresh_viewer_notifications(user)
            return
        if role == "supplier":
            await NotificationService._refresh_supplier_notifications(user)
            return
        if role in {"admin", "manager"}:
            await NotificationService._refresh_manager_admin_brief(user)

    @staticmethod
    async def refresh_operational_alerts():
        await NotificationService._refresh_low_stock_alerts()
        await NotificationService._refresh_expiry_alerts()
        await NotificationService._refresh_delayed_po_alerts()
        await NotificationService._refresh_unfulfilled_sales_order_alerts()

    @staticmethod
    def _role_focus(role: str):
        if role == "viewer":
            return {
                "title": "Track Your Orders",
                "subtitle": "Focus on pending or recently updated orders.",
                "recommended_actions": [
                    "Open order details",
                    "Cancel stale pending orders if needed",
                ],
            }
        if role == "supplier":
            return {
                "title": "Supplier Action Queue",
                "subtitle": "Focus on approved and partially received purchase orders.",
                "recommended_actions": [
                    "Review approved POs",
                    "Update invoice details",
                ],
            }
        return {
            "title": "Operations Control",
            "subtitle": "Focus on critical stock, delayed POs, and pending fulfillment.",
            "recommended_actions": [
                "Prioritize critical alerts",
                "Resolve delayed workflows",
            ],
        }

    @staticmethod
    async def list_notifications(
        user: dict, include_read: bool = False, limit: int = 100
    ):
        await NotificationService.refresh_operational_alerts()
        await NotificationService._refresh_role_specific_alerts(user)

        role = user.get("role", "viewer")
        email = user.get("email", "")
        rows = await NotificationRepository.list_for_user(
            role=role,
            email=email,
            include_read=include_read,
            limit=limit,
        )
        unread_count = await NotificationRepository.count_unread(role, email)
        summary = await NotificationRepository.summarize_for_user(role, email)

        return {
            "items": [notification_model(row) for row in rows],
            "unread_count": unread_count,
            "summary": summary,
            "role_focus": NotificationService._role_focus(role),
            "last_refreshed": datetime.utcnow(),
        }

    @staticmethod
    async def mark_read(notification_id: str, user: dict):
        await NotificationRepository.mark_read(notification_id)
        return await NotificationService.list_notifications(
            user, include_read=False, limit=100
        )

    @staticmethod
    async def mark_all_read(user: dict):
        await NotificationRepository.mark_all_read(
            user.get("role", "viewer"),
            user.get("email", ""),
        )
        return await NotificationService.list_notifications(
            user, include_read=False, limit=100
        )

    @staticmethod
    async def list_logs(user: dict, limit: int = 500):
        if user.get("role") not in {"admin", "manager"}:
            raise PermissionError("Only admin and manager can view notification logs")

        rows = await NotificationRepository.list_logs(limit=limit)
        return [notification_model(row) for row in rows]
