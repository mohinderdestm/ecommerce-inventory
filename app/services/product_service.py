import random
import string
import asyncio
from fastapi import HTTPException
from app.repositories.product_repository import ProductRepository
from app.repositories.warehouse_stock_repository import WarehouseStockRepository
from app.core.websocket_manager import manager
from app.services.warehouse_stock_service import WarehouseStockService
from app.services.audit_service import AuditService


class ProductService:

    @staticmethod
    def generate_sku(prefix="PROD"):
        return f"{prefix}-" + "".join(
            random.choices(string.ascii_uppercase + string.digits, k=6)
        )

    @staticmethod
    def _normalize_allocations(allocations):
        normalized = []
        for allocation in allocations or []:
            warehouse_id = allocation.get("warehouse_id")
            quantity = int(allocation.get("quantity") or 0)
            if warehouse_id and quantity > 0:
                normalized.append({"warehouse_id": warehouse_id, "quantity": quantity})
        return normalized

    @classmethod
    async def _attach_warehouse_stock(cls, products: list[dict]):
        if not products:
            return []

        stock_rows = await WarehouseStockRepository.find_by_product_ids(
            [product["id"] for product in products]
        )
        stock_map = {}

        for row in stock_rows:
            product_id = str(row.get("product_id"))
            variant_sku = row.get("variant_sku")
            key = (product_id, variant_sku)
            entry = stock_map.setdefault(
                key,
                {
                    "total": 0,
                    "warehouses": [],
                },
            )
            quantity = int(row.get("quantity") or 0)
            entry["total"] += quantity
            entry["warehouses"].append(
                {
                    "warehouse_id": str(row.get("warehouse_id")),
                    "warehouse_name": row.get("warehouse_name"),
                    "quantity": quantity,
                }
            )

        enriched_products = []
        for product in products:
            product_copy = dict(product)
            product_copy["low_stock_threshold"] = int(
                product_copy.get("low_stock_threshold") or 5
            )
            base_summary = stock_map.get(
                (product_copy["id"], product_copy.get("sku")),
                {"total": 0, "warehouses": []},
            )
            base_stock = base_summary["total"]
            total_stock = base_stock

            variants = []
            for variant in product_copy.get("variants", []):
                variant_copy = dict(variant)
                variant_summary = stock_map.get(
                    (product_copy["id"], variant_copy.get("sku")),
                    {"total": 0, "warehouses": []},
                )
                variant_stock = variant_summary["total"]
                variant_copy["stock"] = variant_stock
                variant_copy["reorder_level"] = variant_stock
                variant_copy["low_stock_threshold"] = int(
                    variant_copy.get("low_stock_threshold")
                    if variant_copy.get("low_stock_threshold") is not None
                    else product_copy.get("low_stock_threshold", 5)
                )
                variant_copy["warehouse_stock"] = variant_summary["warehouses"]
                total_stock += variant_stock
                variants.append(variant_copy)

            product_copy["base_stock"] = base_stock
            product_copy["stock"] = total_stock
            product_copy["reorder_level"] = total_stock
            product_copy["warehouse_stock"] = base_summary["warehouses"]
            product_copy["variants"] = variants
            enriched_products.append(product_copy)

        return enriched_products

    @classmethod
    async def _assign_warehouse_allocations(
        cls,
        product: dict,
        base_allocations: list[dict],
        variant_allocation_map: dict[str, list[dict]],
        performed_by: dict | None = None,
        reference_type: str = "product_stock_allocation",
        reference_id: str | None = None,
        audit_context: dict | None = None,
    ):
        for allocation in base_allocations:
            await WarehouseStockService.assign_stock_entry(
                allocation["warehouse_id"],
                product,
                product["sku"],
                allocation["quantity"],
                variant_name="Base Product",
                performed_by=performed_by,
                reference_type=reference_type,
                reference_id=reference_id,
                audit_context=audit_context,
            )

        for variant in product.get("variants", []):
            for allocation in variant_allocation_map.get(variant.get("sku"), []):
                await WarehouseStockService.assign_stock_entry(
                    allocation["warehouse_id"],
                    product,
                    variant["sku"],
                    allocation["quantity"],
                    variant_name=variant.get("name", "Variant"),
                    performed_by=performed_by,
                    reference_type=reference_type,
                    reference_id=reference_id,
                    audit_context=audit_context,
                )

    @classmethod
    async def get_product_with_stock(cls, product_id: str):
        product = await ProductRepository.get_product_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        enriched_products = await cls._attach_warehouse_stock([product])
        return enriched_products[0]

    @classmethod
    async def create_product(
        cls, data: dict, user: dict, audit_context: dict | None = None
    ):
        data = dict(data)
        base_allocations = cls._normalize_allocations(
            data.pop("warehouse_allocations", [])
        )
        main_sku = cls.generate_sku()
        data["sku"] = main_sku
        data["status"] = "active"
        data["created_by"] = user.get("id")
        data["supplier_email"] = user.get("email")
        data["reorder_level"] = 0
        data["low_stock_threshold"] = int(data.get("low_stock_threshold") or 5)

        variants = []
        variant_allocation_map = {}
        for raw_variant in data.get("variants", []):
            variant = dict(raw_variant)
            allocations = cls._normalize_allocations(
                variant.pop("warehouse_allocations", [])
            )
            variant["reorder_level"] = 0
            variant["stock"] = 0
            variant["low_stock_threshold"] = int(
                variant.get("low_stock_threshold")
                if variant.get("low_stock_threshold") is not None
                else data.get("low_stock_threshold", 5)
            )

            if not variant.get("sku"):
                variant_suffix = variant.get("name", "VAR").replace(" ", "").upper()[:3]
                variant["sku"] = f"{main_sku}-{variant_suffix}"

            if allocations:
                variant_allocation_map[variant["sku"]] = allocations
            variants.append(variant)

        data["variants"] = variants

        if "image" not in data:
            data["image"] = None

        product = await ProductRepository.create_product(data)
        await cls._assign_warehouse_allocations(
            product,
            base_allocations,
            variant_allocation_map,
            performed_by=user,
            reference_type="product_stock_allocation",
            reference_id=product["id"],
            audit_context=audit_context,
        )
        created_product = await cls.get_product_with_stock(product["id"])

        await AuditService.safe_log_action(
            user=user,
            action="product.create",
            entity_type="product",
            entity_id=product["id"],
            old_value=None,
            new_value=created_product,
            audit_context=audit_context,
        )

        return created_product

    @classmethod
    async def get_products(cls, user: dict):
        user_role = user.get("role")
        supplier_email = None

        if user_role == "supplier":
            supplier_email = user.get("email")

        products = await ProductRepository.get_all_products(
            supplier_email=supplier_email
        )
        return await cls._attach_warehouse_stock(products)

    @classmethod
    async def update_product(
        cls, product_id: str, data: dict, user: dict, audit_context: dict | None = None
    ):
        data = dict(data)
        base_allocations = cls._normalize_allocations(
            data.pop("warehouse_allocations", [])
        )
        existing = await ProductRepository.get_product_by_id(product_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Product not found")

        data["low_stock_threshold"] = int(
            data.get("low_stock_threshold")
            if data.get("low_stock_threshold") is not None
            else existing.get("low_stock_threshold", 5)
        )

        variant_allocation_map = {}
        if "variants" in data and isinstance(data["variants"], list):
            base_sku = existing.get("sku", "PROD-GEN")
            normalized_variants = []

            for raw_variant in data["variants"]:
                variant = dict(raw_variant)
                allocations = cls._normalize_allocations(
                    variant.pop("warehouse_allocations", [])
                )
                variant["reorder_level"] = 0
                variant["stock"] = 0
                variant["low_stock_threshold"] = int(
                    variant.get("low_stock_threshold")
                    if variant.get("low_stock_threshold") is not None
                    else data.get(
                        "low_stock_threshold", existing.get("low_stock_threshold", 5)
                    )
                )

                if not variant.get("sku"):
                    variant_suffix = (
                        variant.get("name", "VAR").replace(" ", "").upper()[:3]
                    )
                    variant["sku"] = f"{base_sku}-{variant_suffix}"
                if allocations:
                    variant_allocation_map[variant["sku"]] = allocations
                normalized_variants.append(variant)

            data["variants"] = normalized_variants

        data["reorder_level"] = 0

        result = await ProductRepository.update_product(product_id, data)

        if not result or result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Product not found")

        updated_product = await ProductRepository.get_product_by_id(product_id)
        await cls._assign_warehouse_allocations(
            updated_product,
            base_allocations,
            variant_allocation_map,
            performed_by=user,
            reference_type="product_stock_update",
            reference_id=product_id,
            audit_context=audit_context,
        )
        updated_product = await cls.get_product_with_stock(product_id)

        await AuditService.safe_log_action(
            user=user,
            action="product.update",
            entity_type="product",
            entity_id=product_id,
            old_value=existing,
            new_value=updated_product,
            audit_context=audit_context,
        )

        asyncio.create_task(
            manager.broadcast({"event": "PRODUCT_UPDATED", "data": updated_product})
        )

        return {"message": "Product updated"}

    @classmethod
    async def delete_product(
        cls, product_id: str, user: dict, audit_context: dict | None = None
    ):
        existing = await ProductRepository.get_product_by_id(product_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Product not found")

        result = await ProductRepository.delete_product(product_id)

        if not result or result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Product not found")

        await AuditService.safe_log_action(
            user=user,
            action="product.delete",
            entity_type="product",
            entity_id=product_id,
            old_value=existing,
            new_value=None,
            audit_context=audit_context,
        )

        asyncio.create_task(
            manager.broadcast({"event": "PRODUCT_DELETED", "data": {"id": product_id}})
        )

        return {"message": "Product deleted successfully"}
