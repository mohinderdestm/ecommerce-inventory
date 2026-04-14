from fastapi import HTTPException
import logging

from app.repositories.variant_repository import VariantRepository
from app.repositories.product_repository import ProductRepository
from app.models.variant import build_variant_document, generate_variant_sku
from app.schemas.variant import VariantCreateRequest, VariantUpdateRequest, VariantBulkCreateRequest

logger = logging.getLogger(__name__)


class VariantService:
    def __init__(self, variant_repo: VariantRepository, product_repo: ProductRepository):
        self.variant_repo = variant_repo
        self.product_repo = product_repo

    # Add Variants 

    async def add_variants(
        self,
        product_id: str,
        payload: VariantBulkCreateRequest,
        created_by: str,
    ) -> dict:
        # Validate product exists
        product = await self.product_repo.find_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found.")

        seen_skus = set()
        docs = []

        for v in payload.variants:
            # SKU — use provided or auto-generate
            sku = v.sku.upper().strip() if v.sku else generate_variant_sku(
                parent_sku=product["sku"],
                color=v.color or "",
                attributes=v.attributes or {},
            )

            # Uniqueness within this batch
            if sku in seen_skus:
                raise HTTPException(
                    status_code=409,
                    detail=f"Duplicate SKU '{sku}' in request."
                )
            # Uniqueness in DB
            if await self.variant_repo.sku_exists(sku):
                raise HTTPException(
                    status_code=409,
                    detail=f"Variant SKU '{sku}' already exists."
                )

            seen_skus.add(sku)
            docs.append(build_variant_document(
                product_id=product_id,
                color=v.color or "",
                attributes=v.attributes or {},
                sku=sku,
                selling_price=v.selling_price,
                cost_price=v.cost_price,
                stock=v.stock,
                image_metadata=[img.model_dump() for img in (v.image_metadata or [])],
                created_by=created_by,
            ))

        created = await self.variant_repo.create_many(docs)
        logger.info(f"{len(created)} variant(s) added to product {product_id} by {created_by}")
        return {"product_id": product_id, "created": len(created), "variants": created}

    # List Variants 

    async def get_variants(
        self,
        product_id: str,
        only_active: bool = False,
        page: int = 1,
        page_size: int = 50,
    ) -> dict:
        product = await self.product_repo.find_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found.")

        skip = (page - 1) * page_size
        variants, total = await self.variant_repo.find_by_product_id(
            product_id=product_id,
            only_active=only_active,
            skip=skip,
            limit=page_size,
        )
        return {"total": total, "product_id": product_id, "variants": variants}

    # Update Variant 

    async def update_variant(
        self,
        product_id: str,
        variant_id: str,
        payload: VariantUpdateRequest,
        updated_by: str,
    ) -> dict:
        # Confirm variant belongs to this product
        variant = await self.variant_repo.find_by_variant_id(variant_id)
        if not variant or variant["product_id"] != product_id:
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
            update_data["image_metadata"] = [i.model_dump() for i in payload.image_metadata]

        if not update_data:
            raise HTTPException(status_code=400, detail="No valid fields provided for update.")

        updated = await self.variant_repo.update(variant_id, update_data)
        logger.info(f"Variant {variant_id} updated by {updated_by}")
        return updated

    # Delete Variant 

    async def delete_variant(self, product_id: str, variant_id: str) -> None:
        variant = await self.variant_repo.find_by_variant_id(variant_id)
        if not variant or variant["product_id"] != product_id:
            raise HTTPException(status_code=404, detail="Variant not found on this product.")
        await self.variant_repo.delete(variant_id)
        logger.info(f"Variant {variant_id} deleted from product {product_id}")