from fastapi import HTTPException
import logging

from app.repositories.product_repository import ProductRepository
from app.models.variant import build_variant_document, generate_variant_sku
from app.schemas.variant import VariantCreateRequest, VariantUpdateRequest, VariantBulkCreateRequest

logger = logging.getLogger(__name__)


class VariantService:
    def __init__(self, product_repo: ProductRepository):
        self.repo = product_repo

    # Add Variants 

    async def add_variants(
        self,
        product_id: str,
        payload: VariantBulkCreateRequest,
        created_by: str,
    ) -> dict:
        product = await self.repo.find_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found.")

        existing_skus = {v["sku"] for v in product.get("variants", [])}
        built_variants = []

        for v in payload.variants:
            # Generate or validate SKU
            if v.sku:
                sku = v.sku.upper().strip()
            else:
                sku = generate_variant_sku(
                    parent_sku=product["sku"],
                    color=v.color or "",
                    attributes=v.attributes or {},
                )

            # Check uniqueness within this product
            if sku in existing_skus:
                raise HTTPException(
                    status_code=409,
                    detail=f"Variant SKU '{sku}' already exists on this product."
                )

            # Check uniqueness across all products
            if await self.repo.variant_sku_exists(sku, exclude_product_id=product_id):
                raise HTTPException(
                    status_code=409,
                    detail=f"Variant SKU '{sku}' already exists on another product."
                )

            existing_skus.add(sku)
            built_variants.append(
                build_variant_document(
                    color=v.color or "",
                    attributes=v.attributes or {},
                    sku=sku,
                    selling_price=v.selling_price,
                    cost_price=v.cost_price,
                    stock=v.stock,
                    image_metadata=[img.model_dump() for img in (v.image_metadata or [])],
                )
            )

        updated = await self.repo.add_variants(product_id, built_variants)
        logger.info(
            f"{len(built_variants)} variant(s) added to product {product_id} by {created_by}"
        )
        return updated

    # Update Variant 

    async def update_variant(
        self,
        product_id: str,
        variant_id: str,
        payload: VariantUpdateRequest,
        updated_by: str,
    ) -> dict:
        product = await self.repo.find_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found.")

        # Confirm variant exists on this product
        variant = next(
            (v for v in product.get("variants", []) if v["variant_id"] == variant_id),
            None
        )
        if not variant:
            raise HTTPException(status_code=404, detail="Variant not found on this product.")

        update_data = {}
        if payload.color is not None:
            update_data["color"] = payload.color.strip()
        if payload.attributes is not None:
            update_data["attributes"] = payload.attributes
        if payload.selling_price is not None:
            update_data["selling_price"] = round(payload.selling_price, 2)
        if payload.cost_price is not None:
            update_data["cost_price"] = round(payload.cost_price, 2)
        if payload.stock is not None:
            update_data["stock"] = payload.stock
        if payload.is_active is not None:
            update_data["is_active"] = payload.is_active
        if payload.image_metadata is not None:
            update_data["image_metadata"] = [img.model_dump() for img in payload.image_metadata]

        if not update_data:
            raise HTTPException(status_code=400, detail="No valid fields provided for update.")

        updated = await self.repo.update_variant(product_id, variant_id, update_data)
        logger.info(f"Variant {variant_id} updated on product {product_id} by {updated_by}")
        return updated

    # Delete Variant 

    async def delete_variant(
        self,
        product_id: str,
        variant_id: str,
    ) -> dict:
        product = await self.repo.find_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found.")

        variant = next(
            (v for v in product.get("variants", []) if v["variant_id"] == variant_id),
            None
        )
        if not variant:
            raise HTTPException(status_code=404, detail="Variant not found on this product.")

        updated = await self.repo.delete_variant(product_id, variant_id)
        logger.info(f"Variant {variant_id} deleted from product {product_id}")
        return updated

    # List Variants

    async def get_variants(self, product_id: str) -> list[dict]:
        product = await self.repo.find_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found.")
        return product.get("variants", [])